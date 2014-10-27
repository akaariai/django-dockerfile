from django_dockerfile import fabfile

def soft_update(image='{{ project_name }}', tag='releases'):
    fabfile._soft_update(image, tag)

def migrate(image='{{ project_name }}', tag='releases'):
    fabfile._migrate(image, tag)

def collect_static(image='{{ project_name }}'):
    fabfile._collect_static(image)

def manage(cmd, image='{{ project_name }}'):
    fabfile._manage(cmd, image)

def hard_update(port, image='{{ project_name }}', tag='releases'):
    fabfile._hard_update(port, image, tag)

def initial_install(image='{{ project_name }}'):
    fabfile._initial_install(image)

def docker_restart(port, image='{{ project_name }}'):
    fabfile._docker_restart(port, image)

def clean_docker():
    fabfile._clean_docker()
