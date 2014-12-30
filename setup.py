#!/usr/bin/env python

from setuptools import setup

setup(name='django_emarsys',
      version='0.6',
      description='Django and Oscar glue for Emarsys events',
      license="MIT",
      author='Markus Bertheau',
      author_email='mbertheau@gmail.com',
      long_description=open('README.md').read(),
      packages=['django_emarsys', 'oscar_emarsys_dashboard'],
      include_package_data=True,
      install_requires=[
          'python-emarsys==0.2'
      ])
