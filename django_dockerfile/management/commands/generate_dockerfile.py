from __future__ import unicode_literals

import os
import shutil
import importlib

from django.core.management import BaseCommand
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        components = []
        for ref in settings.DOCKER_COMPONENTS:
            module_ref, cls_ref = ref.rsplit('.', 1)
            module = importlib.import_module(module_ref)
            cls = getattr(module, cls_ref)
            components.append(cls())
        self.stdout.write("Generating a new dockerfile to ./Dockerfile")
        dockerfile = open('Dockerfile', 'w')
        packages = []
        commands = []
        pre_commands = []
        for component in components:
            dockerfile.write("# From component: %s\n\n" % component.__class__.__name__)
            pre_commands.extend(component.get_pre_commands())
            packages.extend(component.get_packages())
            commands.extend(component.get_post_commands())
            dockerfile.write('\n\n')
        dockerfile.write('\n'.join(pre_commands))
        packages.extend(getattr(settings, 'DOCKER_EXTRA_PACKAGES', []))
        dockerfile.write('apt-get install -y ' + ' '.join(packages))
        dockerfile.write('\n'.join(commands))

        self.stdout.write('Creating default server configuration to ./server_config/')
        if not os.path.isdir('./server_config'):
            os.mkdir('./server_config')
        for component in components:
            files = component.config_files()
            for src in files:
                with open('./server_config/' + os.path.basename(src.name), 'w') as dst:
                    shutil.copyfileobj(src, dst)
                src.close()
            with open('./server_config/supervisord.conf', 'w') as supervisorconf:
                for component in components:
                    supervisorconf.write("# From component: %s\n\n" % component.__class__.__name__)
                    supervisorconf.write(component.supervisord_conf())
                    supervisorconf.write('\n\n')
