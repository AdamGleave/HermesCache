# -*- coding: utf-8 -*-
'''
@author: saaj
'''


try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(
  name             = 'HermesCache',
  version          = '0.5.2',
  author           = 'saaj',
  author_email     = 'mail@saaj.me',
  packages         = ['hermes', 'hermes.backend', 'hermes.test'],
  test_suite       = 'hermes.test',
  url              = 'https://bitbucket.org/saaj/hermes',
  license          = 'LGPL-2.1+',
  description      = 'Python caching library with tag-based invalidation and dogpile effect prevention',
  long_description = open('README.txt', 'rb').read().decode('utf-8'),
  platforms        = ['Any'],
  keywords         = 'python cache tagging redis memcached',
  classifiers      = [
    'Topic :: Software Development :: Libraries',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',    
    'Intended Audience :: Developers'
  ]
)

