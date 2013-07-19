'''
@author: saaj
'''


import importlib
redis = importlib.import_module('redis')

from . import AbstractBackend, AbstractLock


__all__ = 'Lock', 'Backend'


class Lock(AbstractLock):
  '''Key-aware distrubuted lock'''
  
  _lock = None
  '''Redis lock instance'''  
  
  
  def __init__(self, key, client, **kwargs):
    self._lock = client.lock(key, **{
      'timeout' : kwargs.get('lockTimeout', 900),
      'sleep'   : kwargs.get('lockSleep',   0.1)
    })

  def acquire(self, wait = True):
    return self._lock.acquire(wait)

  def release(self):
    self._lock.release()


class Backend(AbstractBackend):
  '''Redis backend implementation'''
  
  client = None
  '''Redis client'''
  
  _options = None
  '''Lock options'''
  
  
  def __init__(self, mangler, **kwargs):
    super(Backend, self).__init__(mangler)
    
    self.client = redis.StrictRedis(**{
      'host'     : kwargs.pop('host',     'localhost'),
      'password' : kwargs.pop('password', None),
      'port'     : kwargs.pop('port',     6379),
      'db'       : kwargs.pop('db',       0)
    })
    
    self._options = kwargs
  
  def lock(self, key):
    return Lock(self.mangler.nameLock(key), self.client, **self._options)
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    if not mapping:
      mapping = {key : value}
    mapping = {k : self.mangler.dumps(v) for k, v in mapping.items()}
    
    if not ttl:
      self.client.mset(mapping)
    else:
      pipeline = self.client.pipeline()
      for k, v in mapping.items():
        pipeline.setex(k, ttl, v)
      pipeline.execute()
  
  def load(self, keys):
    if self._isScalar(keys):
      value = self.client.get(keys)
      if value is not None:
        value = self.mangler.loads(value)
      return value
    else:
      return {k : self.mangler.loads(v) for k, v in zip(keys, self.client.mget(keys)) if v is not None}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    self.client.delete(*keys)

  def clean(self):
    self.client.flushdb()
