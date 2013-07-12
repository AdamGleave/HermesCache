'''
@author: saaj
'''


import collections


class AbstractLock(object):
  '''Abstract lock.'''
    
  def acquire(self, key = None, wait = True):
    raise NotImplementedError()

  def release(self, key = None):
    raise NotImplementedError()
    
    
class AbstractBackend(object):
  '''Abstract backend.'''

  lock = None
  '''Object that provides ``acquire`` and ``release`` functionality. 
  Backend implementation may not the locking object.'''
  

  @staticmethod
  def _isScalar(value):
    return not isinstance(value, (collections.Iterable)) or isinstance(value, basestring)

  def save(self, key = None, value = None, map = None, ttl = None):
    raise NotImplementedError()
  
  def load(self, keys):
    raise NotImplementedError()
  
  def remove(self, keys):
    raise NotImplementedError()
  
  def clean(self):
    raise NotImplementedError()
