from fabric import api
from fabric.contrib import files

import json
import os
import tempfile

from django_dockerfile import generate_dockerfile

api.env.forward_agent = True
loaded_server_env = None

def _ask_env(server_env, path=None):
    if path is None:
        path = []
    for k, v in server_env.items():
        if v is None:
            print(
                'Give value for variable "%s":' % ('__'.join(path + [k])))
            val = raw_input()
            server_env[k] = val
        if isinstance(v, dict):
            server_env[k] = _ask_env(v, path=path + [k])
    return server_env

def _override_env(server_env, **kwargs):
    return server_env

def from_env(env_file, **kwargs):
    server_env = generate_dockerfile._load_env_file(env_file)
    server_env = _override_env(server_env, **kwargs)
    server_env = _ask_env(server_env)
    if not api.env.hosts:
        api.env.hosts = [server_env['server']['host']]
    if server_env['server']['user']:
        api.env.user = server_env['server']['user']
    global loaded_server_env
    loaded_server_env = server_env

def migrate():
    image = loaded_server_env['server']['image']
    api.run('docker exec -i -t %s python manage.py migrate --noinput' % image)

def collect_static():
    image = loaded_server_env['server']['image']
    api.run('docker exec -i -t %s python manage.py collectstatic --noinput' % image)

def manage(cmd):
    image = loaded_server_env['server']['image']
    api.run('docker exec -i -t %s python manage.py %s' % (image, cmd))

def hard_update():
    tag = loaded_server_env['tag']
    image = loaded_server_env['server']['image']
    git_repo = loaded_server_env['git_repo']
    if not files.exists('/tmp/%s' % image):
        with api.cd('/tmp'):
            api.run('git clone %s %s' % (git_repo, image))
    with api.cd('/tmp/%s' % image):
        api.run('git fetch origin')
        api.run('git reset --hard origin/%s' % tag)
        f = tempfile.NamedTemporaryFile()
        f.write(json.dumps(loaded_server_env))
        f.flush()
        tmpdir = tempfile.mkdtemp()
        api.local('python -m django_dockerfile.generate_dockerfile %s %s' % (f.name, tmpdir))
        api.put(os.path.join(tmpdir, 'Dockerfile'), 'Dockerfile')
        api.put(os.path.join(tmpdir, 'server_config'), 'server_config')
        f.close()
        api.run('docker build -t %s .' % image)
        with api.settings(warn_only=True):
            api.run('docker rm -f %s' % image)
    _run_docker()

def _run_docker():
    env = []
    for k, v in loaded_server_env['env'].items():
        env.append('-e \'%s=%s\'' % (k, v))
    env.append('-e \'DOCKER_COMPONENTS=%s\'' % json.dumps(loaded_server_env['components']))
    env = ' '.join(env)
    api.run(
        """
docker run -v /var/docker/{image}:/var/project_state -p {port}:8001 --name={image} -d {env} {image}
        """.format(image=loaded_server_env['server']['image'],
                   port=loaded_server_env['server']['port'],
                   env=env)
    )


def clean_docker():
    with api.settings(warn_only=True):
        api.run('docker rm $(docker ps -a -q)', shell=True)
        api.run('docker rmi $(docker images -q --filter "dangling=true")', shell=True)

def docker_restart():
    image = loaded_server_env['server']['image']
    with api.settings(warn_only=True):
        api.run('docker stop %s' % image)
        api.run('docker rm %s' % image)
    _run_docker()

def logs():
    image = loaded_server_env['server']['image']
    api.run('docker logs %s' % image)
