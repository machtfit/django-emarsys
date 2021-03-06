#!/usr/bin/env python

from setuptools import setup

setup(name='django_emarsys',
      version='0.43',
      description='Django glue for Emarsys events',
      license="MIT",
      author='Markus Bertheau',
      author_email='mbertheau@gmail.com',
      long_description=open('README.md').read(),
      packages=['django_emarsys',
                'django_emarsys.management',
                'django_emarsys.management.commands',
                'django_emarsys.migrations'
                ],
      include_package_data=True,
      install_requires=[
          'jsonfield==2.0.2',
          'future'
      ])
