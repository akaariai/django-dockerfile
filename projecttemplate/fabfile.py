from django_dockerfile.fabfile import *  # noqa

def soft_update(image='{{ project_name }}', tag='releases'):
    _soft_update(image, tag=releases)

def migrate(image='{{ project_name }}', tag='releases'):
    _migrate(image, tag)

def collect_static(image='{{ project_name }}'):
    _collect_static(image)

def manage(cmd, image='{{ project_name }}'):
    _manage(cmd, image)

def hard_update(port, image='{{ project_name }}', tag='releases'):
    _hard_update(port, image, tag)

def intitial_install(image='{{ project_name }}'):
    _initial_install(image)

def docker_restart(port, image='{{ project_name }}'):
    _docker_restart(port, image)
