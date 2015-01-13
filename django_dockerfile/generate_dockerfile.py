# -*- coding: utf-8 -*-

import sys
import os
import shutil

import json
import codecs

"""Backport of importlib.import_module from 3.x."""

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                             "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]

def merge(overrides, to_dictionary):
    new = {}
    for k, v in overrides.items():
        if k not in to_dictionary or not isinstance(to_dictionary[k], dict):
            new[k] = v
        else:
            new[k] = merge(overrides[k], to_dictionary[k])
    for k, v in to_dictionary.items():
        if k in new:
            continue
        new[k] = v
    return new

def _load_env_file(env_file):
    with codecs.open(env_file, 'r', 'UTF-8') as f:
        data = json.loads(f.read())
        found_data = {}
        for f in data.get('from', []):
            from_data = _load_env_file(f)
            # The data in later from files override that from
            # earlier from files
            found_data = merge(from_data, found_data)
        if 'from' in data:
            del data['from']
        # The data in the current file overrides that from
        # the from files.
        return merge(data, found_data)

if __name__ == '__main__':
    print open(sys.argv[1], 'r').read()
    server_env = _load_env_file(sys.argv[1])
    components = []
    for ref in server_env['components']:
        module_ref, cls_ref = ref.rsplit('.', 1)
        module = import_module(module_ref)
        cls = getattr(module, cls_ref)
        components.append(cls())
    print("Generating a new dockerfile")
    dockerfile = open(os.path.join(sys.argv[2], 'Dockerfile'), 'w')
    packages = []
    commands = []
    pre_commands = []
    for component in components:
        pre_commands.extend(component.get_pre_commands())
        packages.extend(component.get_packages())
        commands.extend(component.get_post_commands())
        dockerfile.write('\n\n')
    dockerfile.write('\n'.join(pre_commands))
    packages.extend(server_env.get('packages', []))
    dockerfile.write('\nRUN apt-get install -y ' + ' '.join(packages))
    dockerfile.write('\n')
    dockerfile.write('\n'.join(commands))

    print('Creating server configuration')
    servpath = os.path.join(sys.argv[2], 'server_config')
    if not os.path.isdir(servpath):
        os.mkdir(servpath)
    for component in components:
        files = component.config_files()
        for src in files:
            with open(os.path.join(servpath, os.path.basename(src.name)), 'w') as dst:
                shutil.copyfileobj(src, dst)
            src.close()
        with open(os.path.join(servpath, 'supervisord.conf'), 'w') as supervisorconf:
            for component in components:
                supervisorconf.write("# From component: %s\n\n" % component.__class__.__name__)
                supervisorconf.write(component.supervisord_conf())
                supervisorconf.write('\n\n')
