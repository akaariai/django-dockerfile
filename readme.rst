This project aims to implement a simple way to get up and running with
Django.

The assumption is that you have used a day or two setting up a small
Django project, and now you want to push that project into production.
However, proper production deployment with database setup, static and
media file handling, security, backups and so on isn't an easy thing to
do. In addition, situations where you need to use Python 2.7 but you are
tasked to install the project on RHEL6 based server can be annoying to
solve.

Django-dockerfile assumes your project will:
1. Use git for source control
2. Use PostgreSQL as database
3. Use Linux (or Linux-like machine) for development
4. Use Linux for deployment. The server must have Python 2.6 or Python 2.7,
git and Docker 1.3.0+ installed.

Steps to create a fully working and deployed app.

  1. Create a virtualenv for the project:

         virtualenv my_project_env

  2. Create a new project, use Django 1.7+ for it. Creation:
      
      django-admin.py startproject --template=https://raw.githubusercontent.com/akaariai/django-dockerfile/master/docker-template.tar.gz my_project_name

  3. We assume you have PostgreSQL "somedb" with user "someuser" and password
     "somepassword" set up on localhost. Edit the my_project_env/bin/activate
     file and add the following lines to the end of it::

         export DJANGO_DB_USER=someuser
         export DJANGO_DB_NAME=somedb
         export DJANGO_DB_PASSWORD=somepassword
         export DJANGO_ENVIRONMENT=development

     The first three variables control database connection setup, DJANGO_ENVIRONMENT
     tells Django that you are running in development. Finally git server is needed
     so that fabric can automatically handle deployment.

  4. Activate your virtualenv, install dependencies, and run migrate to test
     your setup works::

         source my_project_env/bin/activate
         cd my_project
         pip install -r requirements.txt
         python manage.py migrate
     
     If the installation of psycopg2 from requirements.txt fails, you must install development
     headers of PostgreSQL. You can install them on Ubuntu by::
         
         sudo apt-get install libpq-dev

  5. Add some code to your project. Once you are happy with your project, we are ready
     to deploy it to a server.
  
  6. Your server environment lives in envs/ subdirectory. The project template contains
     some example environment files. The basic setup is that you have a base env file
     from which your different environments (qs, production, ...) inherit. The example
     base.docker file looks like this::

        {
            "components": ["django_dockerfile.components.DebianJessie"],
            "packages": [],
            "git_repo": "ssh://git@example.com/example",
            "tag": "master",
            "env": {
                "DJANGO_DB_HOST": null,
                "DJANGO_DB_PORT": "5432",
                "DJANGO_DB_NAME": "example",
                "DJANGO_DB_USER": "example_user",
                "DJANGO_DB_PASSWORD": null,
                "DJANGO_SECRET_KEY": null,
                "DJANGO_ALLOWED_HOSTS": ".example.com",
                "DJANGO_ENVIRONMENT": null
            },
            "server": {
                "host": null,
                "port": 8010,
                "image": "example",
                "user": "exampleadmin"
            }
        }

    The components tells which docker components you want to install. DebianJessie
    is all you will need to have Django running on Gunicorn set up. Add in
    "django_dockerfile.components.PostgreSQL" if you want to include PostgreSQL 9.4
    database in the same build.

    The packages contain extra deb packages you want to install to the server. This
    is useful when you want for example include additional development headers for
    your requirements.txt additions.

    The git_repo and tag tells Django which git repo and tag to use to fetch the
    source code. That is, the repo + tag should contain the Django project.

    The env section contains environment variables to be used in your setup. The
    keys should be self-explanatory (the DJANGO_ENVIRONMENT was discussed earlier).

    The server section contains information of where to install the package. The
    host is the remote host to use for installation and user is an user which
    can access that host over ssh. The user must also have rights to use docker
    without sudo (add the user to docker group, restart docker). The port tells
    which port the installation will be available from (that is, after installation
    point your browser to host:port to access your application). Finally the image
    tells which name to use for the docker image.

    When a key has a value null, then a inheriting file must override that value.
    Lets see how inheritance works. The example.com env file contains the following
    code::

        {
            "from": ["envs/base.docker", "/somewhere/example.com.secrets"],
            "server": {
                "host": "example.com"
            },
            "env": {
                "DJANGO_ENVIRONMENT": "production",
                "DJANGO_DB_HOST": "db.example.com",
            }
        }

    The "/somewhere/example.com.secrets/" file contents are::

        {
            "env": {
                "DJANGO_DB_PASSWORD": "some_password",
                "DJANGO_SECRET_KEY": "(o0+@qEXAMPLEakSECRET_KEYkDONOTREUSEi2"
            }
        }

    The way this works is that the from clause loads all the variables from the mentioned
    files. First envs/base.docker variables are loaded. Then the secrets file overrides
    env.DJANGO_DB_PASSWORD and env.DJANGO_SECRET_KEY. Finally the example.com file
    overrides server.host, and env.DJANGO_ENVIRONMENT and env.DJANGO_DB_HOST.

    You can have another file for your qa server, or multiple production servers all
    inheriting from the same base file.

    You shuold edit the env files to match your setup. You can name the files whatever
    way you like.

  7. Commit changes to git.

  8. Deploy to server. The server environment has a couple of assumptions:
       - Docker 1.3.0+ installed and running
       - Docker runnable without sudo commands (add users who should have this
         ability to group docker, restart docker daemon)
       - Non-ancient version of git
       - Python 2.6 or 2.7
  
     When the server is set up, you can start the server by running::

        fab from_file:envs/example.com hard_update

  9. Point your browser to http://example.com:8010 - you should have a complete installation ready!

Note that you can start a bash shell in the container by running `docker exec -i -t my_project /bin/bash`
on the remote server. This is extremely convenient for debugging, but you should avoid doing
configuration changes into the container - the whole idea is that the Dockerfile sets up your
running environment. So, if you want changes to the environment, you should do them into the
docker image, not to an instance of it.
