'''
@author: saaj
'''


import collections


class AbstractLock(object):
  '''Base locking class. Implements context manger protocol. Mocks ``acquire`` and ``release``
  i.e. it always acquires.'''
  
  key = None
  '''Implementation may be key-aware'''

  mangler = None
  '''Key manager responsible for creating keys, hashing and serialzation'''


  def __init__(self, mangler = None):
    self.mangler = mangler

  def __call__(self, key):
    '''To be used in with statement to provide a key to lock'''
    
    self.key = self.mangler.nameLock(key) if self.mangler else key 
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

  lock = None
  '''Subclass or instance of ``AbstractLock``'''
  
  mangler = None
  '''Key manager responsible for creating keys, hashing and serialzation'''
  

  def __init__(self, mangler):
    self.mangler = mangler
    self.lock    = AbstractLock(mangler)
    
  @staticmethod
  def _isScalar(value):
    return not isinstance(value, collections.Iterable) or isinstance(value, basestring)

  def save(self, key = None, value = None, mapping = None, ttl = None):
    raise NotImplementedError()
  
  def load(self, keys):
    raise NotImplementedError()
  
  def remove(self, keys):
    raise NotImplementedError()
  
  def clean(self):
    raise NotImplementedError()
