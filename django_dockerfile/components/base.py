import os
import shlex
import subprocess
import django_dockerfile


class Component(object):
    code_dir = '/home/docker/code'
    state_dir = '/var/project_state'
    config_dir = os.path.join(code_dir, 'server_config')
    source_config_dir = os.path.join(
        os.path.dirname(os.path.abspath(django_dockerfile.__file__)), 'config_files')

    """
    A command consist of following stages parts:
        1) installation of config files
        2) generation of the dockerfile
          - get_pre_commands()
          - get_packages()
          - get_post_commands()
        3) first startup
        4) startup
        5) participation to supervisor config

    Some examples:
        PostgreSQL would install PostgreSQL packages on dockerfile
        generation, and also install the config files inside the dockerfile.
        On first startup (as defined by the persistent /var/project_state/
        directory's contents), PostgreSQL will install the database cluster,
        database user and other similar things inside the database. On
        startup nothing is done. In supervisord PostgreSQL needs to be
        started up.
    """

    def get_pre_commands(self):
        raise NotImplementedError

    def get_packages(self):
        raise NotImplementedError

    def get_post_commands(self):
        raise NotImplementedError

    def on_first_startup(self):
        raise NotImplementedError

    def pre_startup(self):
        return

    def post_startup(self):
        return

    def config_files(self):
        """
        Returns a list of file objects to copy to the server_config
        directory.
        """
        raise NotImplementedError

    def supervisord_conf(self):
        raise NotImplementedError

    @classmethod
    def exec_as_user(cls, username, cmd):
        import pwd
        cmd = shlex.split(cmd)
        uid = None
        if username:
            uid = pwd.getpwnam(username).pw_uid

        def preexec():
            if uid:
                os.setuid(uid)

        process = subprocess.Popen(cmd,
                                   preexec_fn=preexec)
        process.wait()
