# -*- encoding: utf-8 -*-
import os
from setuptools import setup
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
setup(
    name="django-dockerfile",
    version="0.1-dev",
    description="A Dockerfile generator for Django",
    long_description=read('readme.rst'),
    url='https://github.com/akaariai/django-dockerfile',
    license='MIT',
    author=u'Anssi Kääriäinen',
    author_email='akaariai@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=['django_dockerfile']
)
