from __future__ import unicode_literals

import os
import shutil

from django.core.management import BaseCommand
config_files_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_files_dir = os.path.join(config_files_dir, 'config_files')

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # Generate server_config directory
        if not os.path.isfile('./server_config/'):
            self.stdout.write('Copying default server configuration to ./server_config/')
            shutil.copytree(config_files_dir, './server_config/')

        self.stdout.write("Generating a new dockerfile to ./Dockerfile")
        dockerfile = open('Dockerfile', 'w')

        def dprint(str):
            dockerfile.write(str + '\n')

        dprint("FROM debian:jessie")
        dprint("MAINTAINER Anssi Kaariainen")  # TODO: Use project's maintainer...
        dprint("# Set locale for the image")
        dprint('RUN echo "deb http://us.archive.ubuntu.com/ubuntu/ '
               'precise-updates main restricted" | '
               'tee -a /etc/apt/sources.list.d/precise-updates.list')
        dprint('RUN apt-get -qq update')
        dprint('RUN apt-get install -y locales')
        # TODO: use settings.py locale instead!
        dprint('RUN echo en_US.UTF-8 UTF-8 > /etc/locale.gen')
        dprint('RUN locale-gen')
        dprint('ENV LC_ALL en_US.UTF-8')
        dprint('ENV LANG en_US.UTF-8')
        dprint('ENV LANGUAGE en_US')
        # TODO: is this dangerous to set globally? We need this so that
        # for example management commands run outside of docker actually work.
        dprint('ENV PYTHONIOENCODING utf-8')

        # We need python-dev, libpq-dev etc so that we can build psycopg2
        # git is needed to fetch the actual running code
        dprint('RUN apt-get install -y build-essential git python python-dev python-setuptools '
               '    libpq-dev supervisor')
        dprint('RUN easy_install pip')
        # Install postgresql
        dprint("RUN apt-get install -y postgresql-9.4 postgresql-client-9.4 postgresql-contrib-9.4")
        # DB configuration happens in run.sh
        # Add requirements separately - allows caching them when they haven't changed.
        requirements_file = None
        if os.path.isfile('./prod_env/requirements-prod.txt'):
            dprint('ADD ./prod_env/requirements-prod.txt '
                   '/home/docker/code/prod_env/requirements-prod.txt')
            requirements_file = '/home/docker/code/prod_env/requirements-prod.txt'
        if os.path.isfile('./requirements.txt'):
            dprint('ADD ./requirements.txt /home/docker/code/requirements.txt')
            if requirements_file is None:
                requirements_file = '/home/docker/code/requirements.txt'
        if requirements_file is None:
            raise Exception("No requirements.txt file found!")
        dprint('RUN pip install -r %s' % requirements_file)
        # We need supervisor so that we can startup both postgresql and gunicorn at startup.
        # Now we are ready to migrate our database.
        dprint('ADD . /home/docker/code/')
        dprint('WORKDIR /home/docker/code/')
        dprint('VOLUME /var/project_state/')
        dprint('RUN chmod a+x /home/docker/code/server_config/run.sh')
        dprint('CMD ["/home/docker/code/server_config/run.sh"]')
