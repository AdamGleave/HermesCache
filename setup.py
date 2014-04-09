from distutils.core import setup

setup(
  name             = 'HermesCache',
  version          = '0.4.0',
  author           = 'saaj',
  author_email     = 'mail@saaj.me',
  packages         = ['hermes', 'hermes.backend', 'hermes.test'],
  url              = 'http://code.google.com/p/hermes-py/',
  license          = 'LGPL',
  description      = 'Python caching library with tag-based invalidation and dogpile effect prevention',
  long_description = open('README.txt').read(),
  platforms        = ['Any'],
  classifiers      = [
    'Topic :: Utilities',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',    
    'Intended Audience :: Developers'
  ]
)