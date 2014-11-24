import os
import shutil

from .base import Component

class PostgreSQL(Component):
    data_dir = os.path.join(Component.state_dir, 'postgres')
    bin_dir = '/usr/lib/postgresql/9.4/bin'

    def get_pre_commands(self):
        return []

    def get_post_commands(self):
        return []

    def get_packages(self):
        return ["postgresql-9.4", "postgresql-client-9.4", "postgresql-contrib-9.4"]

    def on_first_startup(self):
        import pwd
        import grp
        django_db_password = os.environ['DJANGO_DB_PASSWORD']
        django_db_user = os.environ['DJANGO_DB_USER']
        django_db_name = os.environ['DJANGO_DB_NAME']
        if os.path.isfile(os.path.join(self.data_dir, 'installed_marker')):
            raise Exception('PostgreSQL seems to be installed already on first run!')
        shutil.rmtree(self.data_dir, ignore_errors=True)
        os.makedirs(self.data_dir)
        uid = pwd.getpwnam("postgres").pw_uid
        gid = grp.getgrnam("postgres").gr_gid
        os.chown(self.data_dir, uid, gid)
        self.pre_startup()
        self.exec_as_user('postgres', '%s/initdb -D %s' % (self.bin_dir, self.data_dir))
        shutil.copy('%s/pg_hba.conf' % self.config_dir,
                    '%s/pg_hba.conf' % self.data_dir)
        shutil.copy('%s/postgresql.conf' % self.config_dir,
                    '%s/postgresql.conf' % self.data_dir)
        self.exec_as_user(
            'postgres',
            '%s/pg_ctl -w -D %s -l %s/logs/postgresql.log start' %
            (self.bin_dir, self.data_dir, self.state_dir))
        self.exec_as_user(
            'postgres',
            '%s/psql --command "CREATE USER %s WITH PASSWORD \'%s\';" ' %
            (self.bin_dir, django_db_user, django_db_password))
        self.exec_as_user(
            'postgres',
            '%s/createdb -O %s %s' %
            (self.bin_dir, django_db_user, django_db_name))
        self.exec_as_user(
            'postgres',
            '%s/pg_ctl -w -D %s -l %s/logs/postgresql.log stop' %
            (self.bin_dir, self.data_dir, self.state_dir))

    def pre_startup(self):
        if os.path.isfile('/var/run/postgresql'):
            os.chmod('/var/run/postgresql', '2775')
        else:
            self.exec_as_user(None, 'install -d -m 2775 -o postgres '
                              '-g postgres /var/run/postgresql')

    def config_files(self):
        return [open('%s/pg_hba.conf' % self.source_config_dir, 'r'),
                open('%s/postgresql.conf' % self.source_config_dir, 'r')]

    def supervisord_conf(self):
        return """
[program:postgresql]
command=%s/postgres -D %s
user=postgres
autorestart=true
priority=1000
""" % (self.bin_dir, self.data_dir)
