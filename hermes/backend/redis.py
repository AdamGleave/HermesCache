'''
@author: saaj
'''


import redis

from . import AbstractBackend, BaseLock


class RedisLock(BaseLock):
  '''Key-aware distrubuted lock'''
  
  lock = None
  '''Redis lock instance'''  
  
  
  def __init__(self, mangler, client, **kwargs):
    super(RedisLock, self).__init__(mangler)
    
    self.lock = client.lock(None, **kwargs)

  def acquire(self, wait = True):
    self.lock.name = self.key
    return self._lock.acquire(wait)

  def release(self):
    self._lock.release()


class Redis(AbstractBackend):
  '''Redis backend implementation'''
  
  client = None
  '''Redis client'''
  
  
  def __init__(self, mangler, **kwargs):
    super(Redis, self).__init__(mangler)
    
    self.client = redis.StrictRedis(**{
      'host'     : kwargs.get('host',     'localhost'),
      'password' : kwargs.get('password', None),
      'port'     : kwargs.get('port',     6379),
      'db'       : kwargs.get('db',       0)
    })
    
    self.lock = RedisLock(self.mangler, self.client, **{
      'timeout' : kwargs.get('lockTimeout', None),
      'sleep'   : kwargs.get('lockSleep',   0.1)
    })
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    if not mapping:
      mapping = {key : value}
    mapping = {k : self.mangler.dump(v) for k, v in mapping.items()}
    
    if not ttl:
      self.client.mset(mapping)
    else:
      pipeline = self.client.pipeline()
      for k, v in mapping.items():
        pipeline.setex(k, ttl, v)
      pipeline.execute()
  
  def load(self, keys):
    if self._isScalar(keys):
      value = self.cache.get(keys, None)
      if value is not None:
        value = self.mangler.load(value)
      return value
    else:
      return {k : self.mangler.load(v) for k, v in zip(keys, self.client.mget(keys)) if v is not None}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    self.client.delete(*keys)

  def clean(self):
    self.client.flushdb()
