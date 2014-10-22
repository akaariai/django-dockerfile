# Base setup for debian:jessie based container image
# with python and gunicorn support.

from .base import Component
import os

class DebianJessie(Component):
    def dockerfile(self):
        buffer = []
        w = buffer.append
        w("FROM debian:jessie")
        w("MAINTAINER Anssi Kaariainen")  # TODO: Use project's maintainer...
        w("# Set locale for the image")
        w('RUN echo "deb http://us.archive.ubuntu.com/ubuntu/ '
          'precise-updates main restricted" | '
          'tee -a /etc/apt/sources.list.d/precise-updates.list')
        w('RUN apt-get -qq update')
        w('RUN apt-get install -y locales')
        # TODO: use settings.py locale instead!
        w('RUN echo en_US.UTF-8 UTF-8 > /etc/locale.gen')
        w('RUN locale-gen')
        w('ENV LC_ALL en_US.UTF-8')
        w('ENV LANG en_US.UTF-8')
        w('ENV LANGUAGE en_US')
        # TODO: is this dangerous to set globally? We need this so that
        # for example management commands run outside of docker actually work.
        w('ENV PYTHONIOENCODING utf-8')

        # We need python-dev, libpq-dev etc so that we can build psycopg2
        # git is needed to fetch the actual running code
        w('RUN apt-get install -y build-essential git python python-dev python-setuptools '
          '    libpq-dev supervisor')
        w('RUN easy_install pip')
        # Add requirements separately - allows caching them when they haven't changed.
        requirements_file = None
        if os.path.isfile('./prod_env/requirements-prod.txt'):
            w('ADD ./prod_env/requirements-prod.txt '
              '/home/docker/code/prod_env/requirements-prod.txt')
            requirements_file = '/home/docker/code/prod_env/requirements-prod.txt'
        if os.path.isfile('./requirements.txt'):
            w('ADD ./requirements.txt /home/docker/code/requirements.txt')
            if requirements_file is None:
                requirements_file = '/home/docker/code/requirements.txt'
        if requirements_file is None:
            raise Exception("No requirements.txt file found!")
        w('RUN pip install -r %s' % requirements_file)
        w('ADD . /home/docker/code/')
        w('WORKDIR /home/docker/code/')
        w('VOLUME /var/project_state/')
        w('RUN chmod a+x /home/docker/code/server_config/run.sh')
        w('CMD ["/home/docker/code/server_config/run.sh"]')
        return '\n'.join(buffer)

    def on_first_startup(self):
        import os
        os.makedirs('/var/project_state/logs/supervisord_childs')
        os.chmod('/var/project_state/logs/', 0777)

    def post_startup(self):
        curdir = os.getcwd()
        try:
            os.chdir(self.code_dir)
            for i in range(0, 5):
                from django.db import connection
                try:
                    connection.cursor().execute("select 1")
                except Exception as e:
                    print("DB not running yet, error was: " + str(e))
                    import time
                    time.sleep(1)
            self.exec_as_user(None, "python manage.py migrate --noinput")
            self.exec_as_user(None, "python manage.py collectstatic --noinput")
        finally:
            os.chdir(curdir)

    def config_files(self):
        return [open('%s/gunicorn_config.py' % self.source_config_dir, 'r'),
                open('%s/run.sh' % self.source_config_dir, 'r')]

    def supervisord_conf(self):
        project_name = os.path.basename(os.path.normpath(os.getcwd()))
        return """
; supervisor config file

[unix_http_server]
file=/var/run/supervisor.sock   ; (the path to the socket file)
chmod=0700                       ; sockef file mode (default 0700)

[supervisord]
logfile=/var/project_state/logs/supervisord.log ; (main log file;default $CWD/supervisord.log)
pidfile=/var/run/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/project_state/logs/supervisord_childs/            ; ('AUTO' child log dir, default $TEMP)

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock ; use a unix:// URL  for a unix socket

[program:gunicorn]
command=/usr/local/bin/gunicorn %s.wsgi:application -c /home/docker/code/server_config/gunicorn_config.py
directory=/home/docker/code
user=nobody
autostart=true
autorestart=true
redirect_stderr=true
priority=1
""" % project_name  # noqa
