#!/usr/bin/env python
from setuptools import setup, find_packages
import django_azure


setup(
      name='django-azure',
      version = django_azure.__version__,
      description='Azure storage for Django',
      long_description=open('README.rst', 'rt').read(),
      author='elorus',
      author_email='info@elorus.com',
      packages=find_packages(),
      license='BSD',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries'
        ],
      include_package_data = True,
      install_requires = [
        "Django>=1.6",
        "azure==0.10.1"
        ],
)
