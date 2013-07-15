'''
@author: saaj
'''


import collections


class BaseLock(object):
  '''Base locking class. Implements context manger protocol. Mocks ``acquire`` and ``release``
  i.e. it always acquires.'''
  
  key = None
  '''Implementation may be key-aware'''


  def __call__(self, key):
    '''To be used in with statement to provide a key to lock'''
    
    self.key = key
    return self

  def __enter__(self):
    self.acquire()

  def __exit__(self, type, value, traceback):
    self.release()
    
  def acquire(self, wait = True):
    return True

  def release(self):
    pass


class AbstractBackend(object):
  '''Abstract backend'''

  lock = BaseLock()
  '''Subclass or instance of ``BaseLock``'''
  

  @staticmethod
  def _isScalar(value):
    return not isinstance(value, collections.Iterable) or isinstance(value, basestring)

  def save(self, key = None, value = None, map = None, ttl = None):
    raise NotImplementedError()
  
  def load(self, keys):
    raise NotImplementedError()
  
  def remove(self, keys):
    raise NotImplementedError()
  
  def clean(self):
    raise NotImplementedError()
