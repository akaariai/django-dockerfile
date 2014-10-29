import tempfile

import os
from fabric import api
from fabric.contrib import files

api.env.forward_agent = True

def _soft_update(image, tag='releases',):
    api.local('git archive %s -o /tmp/%s.tar.gz' % (tag, image))
    api.put('/tmp/%s.tar.gz' % image, '/var/docker/%s/tmp/%s.tar.gz' % (image, image))
    api.run('docker exec -i -t %s tar -xzf /var/project_state/tmp/%s.tar.gz' % (image, image))
    _migrate(image=image)
    _collect_static(image=image)
    api.run('docker exec -i -t %s supervisorctl restart gunicorn' % image)

def _migrate(image):
    api.run('docker exec -i -t %s python manage.py migrate --noinput' % image)

def _collect_static(image):
    api.run('docker exec -i -t %s python manage.py collectstatic --noinput' % image)

def _manage(cmd, image):
    api.run('docker exec -i -t %s python manage.py %s' % (image, cmd))

def _hard_update(port, image, tag='releases'):
    if not files.exists('/tmp/%s' % image):
        with api.cd('/tmp'):
            api.run('git clone %s %s' % (os.environ['DJANGO_GIT_UPSTREAM_REPO'], image))
    with api.cd('/tmp/%s' % image):
        api.run('git fetch origin')
        api.run('git reset --hard origin/%s' % tag)
        api.run('docker build -t %s .' % image)
        with api.settings(warn_only=True):
            api.run('docker rm -f %s' % image)
        api.run('/var/docker/%s/docker_run.sh %s %s' % (image, image, port))

def _clean_docker():
    with api.settings(warn_only=True):
        api.run('docker rm $(docker ps -a -q)', shell=True)
        api.run('docker rmi $(docker images -q --filter "dangling=true")', shell=True)

def _initial_install(image):
    if not files.exists('/var/docker/%s' % image):
        api.sudo('mkdir -p /var/docker/%s' % image)
        api.sudo('chown root:docker /var/docker/%s' % image)
        api.sudo('chmod g+w /var/docker/%s' % image)
    print("Gimme environment parameters for the new image. One env param per line."
          "Empty line stops processing")
    vars = []
    while True:
        val = raw_input()  # noqa
        if not val:
            break
        vars.append('-e "%s"' % val)
    environ = ' '.join(vars)
    f = tempfile.NamedTemporaryFile()
    f.write("""#!/bin/bash
# Usage: ./docker_run.sh image_name host_port, for example
# ./docker_run.sh my_project 8004
docker run -v /var/docker/$1:/var/project_state -p $2:8001 --name=$1 -d %s $1
""" % environ)
    api.put(f, '/var/docker/%s/docker_run.sh' % image)
    api.run('chmod a+x /var/docker/%s/docker_run.sh' % image)

def _docker_restart(port, image):
    with api.settings(warn_only=True):
        api.run('docker stop %s' % image)
        api.run('docker rm %s' % image)
    api.run('/var/docker/%s/docker_run.sh %s %s' % (image, image, port))
