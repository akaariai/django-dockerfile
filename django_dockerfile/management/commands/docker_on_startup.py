from __future__ import unicode_literals
import os
import subprocess
import shutil
from django.conf import settings
import importlib
import glob

from django.core.management import BaseCommand

config_files_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_files_dir = os.path.join(config_files_dir, 'config_files')
currdir = os.getcwd()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        components = []
        for ref in settings.DOCKER_COMPONENTS:
            module_ref, cls_ref = ref.rsplit('.', 1)
            module = importlib.import_module(module_ref)
            cls = getattr(module, cls_ref)
            components.append(cls())
        if not os.path.isfile('/var/project_state/__initialized.marker.DO_NOT_DELETE'):
            files = glob.glob('/var/project_state/*')
            for f in files:
                if 'docker_run.sh' in f:
                    continue
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
            for component in components:
                component.on_first_startup()
                open('/var/project_state/__initialized.marker.DO_NOT_DELETE', 'w').close()
        for cls in components:
            cls.pre_startup()
        process = subprocess.Popen(
            ['/usr/bin/supervisord', '-n', '-c',
                '/home/docker/code/server_config/supervisord.conf'],
            stderr=subprocess.STDOUT)
        for cls in components:
            cls.post_startup()
        process.wait()
