command = '/usr/bin/gunicorn'
pythonpath = '/home/docker/code/'
bind = '0.0.0.0:8001'
workers = 3
user = 'nobody'
errorlog = '/var/project_state/logs/gunicorn_error.log'
accesslog = '/var/project_state/logs/gunicorn_access.log'
