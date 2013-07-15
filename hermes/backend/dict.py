'''
@author: saaj
'''


import threading

from . import AbstractBackend, BaseLock


class ThreadLock(BaseLock):
  '''Key-unaware thread lock'''
  
  def __init__(self, mangler = None):
    super(ThreadLock, self).__init__(mangler)
    
    self.lock = threading.Lock()

  def acquire(self, wait = True):
    return self.lock.acquire(wait)

  def release(self):
    self.lock.release()


class Dict(AbstractBackend):
  '''Test purpose backend implementation. Does not implement entry expiry.'''
  
  
  cache = None
  '''A dict intance'''
  
  
  def __init__(self, mangler):
    super(Dict, self).__init__(mangler)
    
    self.lock  = ThreadLock(mangler)
    self.cache = {}
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    if not mapping:
      mapping = {key : value}

    self.cache.update({k : self.mangler.dump(v) for k, v in mapping.items()})
  
  def load(self, keys):
    if self._isScalar(keys):
      value = self.cache.get(keys, None)
      if value is not None:
        value = self.mangler.load(value)
      return value
    else:
      return {k : self.mangler.load(self.cache[k]) for k in keys if k in self.cache}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    map(lambda key: self.cache.pop(key, None), keys)

  def clean(self):
    self.cache.clear()
