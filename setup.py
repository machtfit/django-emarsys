from distutils.core import setup

setup(name='django_emarsys',
      version='0.1.0',
      description='Django and Oscar glue for Emarsys events',
      license="MIT",
      author='Markus Bertheau',
      author_email='mbertheau@gmail.com',
      long_description=open('README.md').read(),
      packages=['django_emarsys', 'oscar_emarsys_dashboard'],
      install_requires=[
          'python-emarsys<=0.2'
      ])
