#!/bin/bash
export CONFIG_FILES_DIR='/home/docker/code/server_config'
export PROJECT_STATE_DIR='/var/project_state'
export POSTGRES_BIN_DIR='/usr/lib/postgresql/9.4/bin'

# Check that /var/run/postgresql exists and has correct permissions. Shameless
# copy from Ubuntu's PostgreSQL setup files
if [ -d /var/run/postgresql ]; then
    chmod 2775 /var/run/postgresql
else
    install -d -m 2775 -o postgres -g postgres /var/run/postgresql
fi

# Check if /var/project_state has been initialized
if [ ! -f $PROJECT_STATE_DIR/initialized.marker ]; then
    rm -rf $PROJECT_STATE_DIR/*
    mkdir -p $PROJECT_STATE_DIR/postgres
    chown postgres:postgres $PROJECT_STATE_DIR/postgres
    mkdir $PROJECT_STATE_DIR/logs
    mkdir -p $PROJECT_STATE_DIR/logs/supervisord_childs/
    chmod a+xw $PROJECT_STATE_DIR/logs
    su postgres -c '$POSTGRES_BIN_DIR/initdb -D $PROJECT_STATE_DIR/postgres'
    cp $CONFIG_FILES_DIR/pg_hba.conf $PROJECT_STATE_DIR/postgres/pg_hba.conf
    cp $CONFIG_FILES_DIR/postgresql.conf $PROJECT_STATE_DIR/postgres/postgresql.conf
    su postgres -c '$POSTGRES_BIN_DIR/pg_ctl -w -D $PROJECT_STATE_DIR/postgres -l $PROJECT_STATE_DIR/logs/postgresql.log start'
    su postgres -c "$POSTGRES_BIN_DIR/psql --command \"CREATE USER $DJANGO_DB_USER WITH PASSWORD '$DJANGO_DB_PASSWORD';\""
    su postgres -c '$POSTGRES_BIN_DIR/createdb -O $DJANGO_DB_USER $DJANGO_DB_NAME UTF8'
    cd /home/docker/code
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    su postgres -c '$POSTGRES_BIN_DIR/pg_ctl -w -D $PROJECT_STATE_DIR/postgres -l $PROJECT_STATE_DIR/logs/postgres/postgresql.log stop'
    touch /var/project_state/initialized.marker
fi

# Start supervisord, which in turn will take care of starting gunicorn,
# postgresql and other possible dependencies
/usr/bin/supervisord -n -c /home/docker/code/server_config/supervisord.conf
