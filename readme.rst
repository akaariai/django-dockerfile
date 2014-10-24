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
3. Use Linux (or Linux like machine) for development
4. Use Linux for deployment (Docker 1.3.0+ required!)

  1. Create a virtualenv for the project (this is not mandatory, but will make
     handling env variables a *lot* easier later on).

         virtualenv my_project_env

  2. Create a new project, use Django 1.7+ for it. Creation:
      
      django-admin.py startproject --template=https://raw.githubusercontent.com/akaariai/django-dockerfile/master/docker-template.tar.gz my_project_name

  3. We assume you have PostgreSQL "somedb" with user "someuser" and password
     "somepassword" set up on localhost. Edit the my_project_env/bin/activate
     file and add the following lines to the end of it:

         export DJANGO_DB_USER=someuser
         export DJANGO_DB_NAME=somedb
         export DJANGO_DB_PASSWORD=somepassword
         export DJANGO_ENVIRONMENT=development
         export GIT_UPSTREAM_REPO=ssh://git@example.com/my_project

     The first three variables control database connection setup, DJANGO_ENVIRONMENT
     tells Django that you are running in development. Finally git server is needed
     so that fabric can automatically handle deployment.

  4. Activate your virtualenv, install dependencies, and run migrate to test
     your setup works.

         source my_project_env/bin/activate
         cd my_project
         pip install -r requirements.txt
         python manage.py migrate
     
     The installation of psycopg2 requires availability of PostgreSQL's library
     headers. You can install them on ubuntu by
         
         sudo apt-get install libpq-dev

  5. Add some code to your project. Once you are happy with your project, we are ready
     to deploy it to a server.
  
  6. Create a dockerfile for the project by runnig python manage.py generate_dockerfile. This
     will also create a server_config directory containing a couple of configuration files and
     other necessary files for the installation to run correctly.
  
  7. Commit changes to git.

  8. Deploy to server. The server environment has a couple of assumptions:
       - Docker 1.3.0+ installed and running
       - Docker runnable without sudo commands (add users who should have this
         ability to group docker, restart docker daemon)
       - Directory /var/docker/my_project created and writable by group docker.
  
     Once those are handled, you will still need to do some initial setup on server:

         fab initial_install:tag=master -H host.example.com -u server_user

     This will build an image, and create file /var/docker/my_project/docker_run.sh on the server.
     The command will ask you for environment variables to add to the command.

     Once this is done, you can start the server by running:

        fab hard_update:tag=master,port=8004 -H host.example.com -u server_user

  9. Point your browser to http://host.example.com:8004 - you should have a complete installation ready!

If you want to install a testing server, this is doable by repeating steps 8 and 9. You will need
to add a new directory to the server (for example /var/docker/my_project_qa), and tell docker to use
that directory by adding parameter image=my_project_qa to the fab commands.

Note that you can start a bash shell in the container by running `docker exec -i -t my_project /bin/bash`.
This is extremely convenient for debugging, but you should avoid doing configuration changes into the
container - the whole idea is that the Dockerfile + run.sh sets up your running environment. So, if
you want changes to the environment, you should do them into the docker image, not to an instance
of it.

This involved a couple of steps, but we have achieved the following things:

Fully repeatable installation on *any* server with Docker 1.3.0+. A quick way
to install qa/testing versions with a couple of commands.
