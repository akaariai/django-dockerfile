This project aims to implement a simple way to get up and running with
Django.

The assumption is that you have used a day or two setting up a small
Django project, and now you want to push that project into production.
However, proper production deployment with database setup, static and
media file handling, security, backups and so on isn't an easy thing to
do. In addition, situations where you need to use Python 2.7 but you are
tasked to install the project on RHEL6 based server can be annoying to
solve.

Django-dockerfile aims to provide users with an easy, yet secure production
setup procedure. Unfortunately, we aren't there yet. Below are the steps needed
to setup the project using docker:

  1. Create a new project, use Django 1.7+ for it.
  2. Add some code to it. Use PostgreSQL. Assumption is that you use virtualenv and
     requirements.txt in project root. Change your settings to use environment variables
     for database config. For example
         
        DATABASES['default']['password'] = os.environ['DJANGO_DB_PASSWORD']. 

     django-dockerfile will need the following environment parameters:

       - DJANGO_DB_NAME: the database name
       - DJANGO_DB_USER: the database user
       - DJANGO_DB_PASSWORD: the database password

     Hint: add these parameters to your virtualenvdir/bin/activate script!
  3. Add dj-static to your requirements.txt, configure your project_name/wsgi.py to use
     dj-static (google directions for that...)
  4. Install django-dockerfile (add it to INSTALLED_APPS, too)
  5. Create a dockerfile for the project by runnig python manage.py generate_dockerfile. This
     will also create a server_config directory containing a couple of configuration files for
     the server, plus run.sh, a file that is responsible for doing setup of your project.
  6. Transfer your project (including the dockerfile) to a production server having Docker 1.3.0+
     installed (earlier versions might work, but you'll want 1.3.0+ for docker exec command).
  7. Run "docker build -t my_project_name ." This will take a while to build.
  8. The project uses environment variables for configuration parameters. The supported parameters
     were listed in step 2 above.
     For each parameter add -e "PARAMETER_NAME=value" to the below command. The example command below
     can be used as skeleton:

      docker -p 8001:8001 -v some_directory_on_server:/var/project_state
             -e "DJANGO_DB_NAME=my_project_db" -e "DJANGO_DB_USER=my_db_user" -e "DJANGO_DB_PASSWORD=secret"
             -d --name=my_project_name my_project_name

     Above some_directory_on_server should be an empty directory on your server. The docker container
     will use that directory for persistent data (most notable database data files).

     Note that the database and the user will be created inside the docker container, set up is
     done by run.sh mentinoned in step 2.

  9. Point your browser to http://server.url:8001 - you should have a complete installation ready!

Note that you can start a bash shell in the container by running `docker exec -i -t my_project_name /bin/bash`.
This is extremely convenient for debugging, but you should avoid doing configuration changes into the
container - the whole idea is that the Dockerfile + run.sh sets up your running environment. So, if
you want changes to pg_hba.conf

TODO: Most important thing is to make the script generation a bit saner: what if you want solr and
memcached installed, or you want to use external database? Also, it would be extremely convenient
to implement a backup command and reload command, which would backup and reload all state data
from your server.
