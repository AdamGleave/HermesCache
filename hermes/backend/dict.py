'''
@author: saaj
'''


import threading

from . import AbstractBackend, AbstractLock


__all__ = 'Lock', 'Backend'


class Lock(AbstractLock):
  '''Key-unaware thread lock'''
  
    
  _lock = None
  '''Threading lock instance'''  
  
  def __init__(self, key):
    self._lock = threading.RLock()

  def acquire(self, wait = True):
    return self._lock.acquire(wait)

  def release(self):
    self._lock.release()


class Backend(AbstractBackend):
  '''Test purpose backend implementation. Does not support entry expiry. ``save`` and ``delete``
  are not atomic in general. Though because writes are synchronized it may be suitable for 
  limited number of real cases with small cached entry size.'''
  
  
  cache = None
  '''A dict intance'''
  
  _lock = None
  '''Lock instance'''
  
  
  def __init__(self, mangler, **kwargs):
    super(Backend, self).__init__(mangler)
    
    self.cache = {}
    self._lock = Lock(None)
  
  def lock(self, key):
    return self._lock
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    if not mapping:
      mapping = {key : value}

    self.cache.update({k : self.mangler.dumps(v) for k, v in mapping.items()})
  
  def load(self, keys):
    if self._isScalar(keys):
      value = self.cache.get(keys, None)
      if value is not None:
        value = self.mangler.loads(value)
      return value
    else:
      return {k : self.mangler.loads(self.cache[k]) for k in keys if k in self.cache}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    for key in keys:
      self.cache.pop(key, None)  

  def clean(self):
    self.cache.clear()
    
  def dump(self):
    return {k : self.mangler.loads(v) for k, v in self.cache.items()}

