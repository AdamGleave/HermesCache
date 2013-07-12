'''
@author: saaj
'''


import threading

from . import AbstractBackend, AbstractLock


class Lock(AbstractLock):
  '''Key-unaware thread lock.'''
  
  _lock = None
  
    
  def __init__(self):
    self._lock = threading.Lock()

  def acquire(self, key = None, wait = True):
    return self._lock.acquire(wait)

  def release(self, key = None):
    self._lock.release()
    

class Dict(AbstractBackend):
  '''Test purpose backend implementation. Does not implement entry expiry'''
  
  
  cache = None
  '''A dict intance'''
  
  
  def __init__(self):
    self.lock  = Lock()
    self.cache = {}
  
  def save(self, key = None, value = None, map = None, ttl = None):
    if not map:
      self.cache[key] = value
    else:
      self.cache.update(map)
  
  def load(self, keys):
    if self._isScalar(keys):
      return self.cache.get(keys, None)
    else:
      return {k : self.cache[k] for k in keys if k in self.cache}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    map(lambda key: self.cache.pop(key, None), keys)

  def clean(self):
    self.cache.clear()
