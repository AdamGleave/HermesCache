'''
@author: saaj
@note: named *redispy* instead of *redis* because confilicts under test environment
'''


from . import AbstractBackend, AbstractLock

import redis


class Lock(AbstractLock):
  '''Key-aware distrubuted lock'''
  
  lock = None
  '''Redis lock instance'''  
  
  
  def __init__(self, mangler, client, **kwargs):
    super(Lock, self).__init__(mangler)
    
    self.lock = client.lock(self.key, **kwargs)

  def __call__(self, key):
    self.lock.name = self.mangler.nameLock(key) 
    return self

  def acquire(self, wait = True):
    return self.lock.acquire(wait)

  def release(self):
    self.lock.release()


class Backend(AbstractBackend):
  '''Redis backend implementation'''
  
  client = None
  '''Redis client'''
  
  
  def __init__(self, mangler, **kwargs):
    super(Backend, self).__init__(mangler)
    
    self.client = redis.StrictRedis(**{
      'host'     : kwargs.get('host',     'localhost'),
      'password' : kwargs.get('password', None),
      'port'     : kwargs.get('port',     6379),
      'db'       : kwargs.get('db',       0)
    })
    
    self.lock = Lock(self.mangler, self.client, **{
      'timeout' : kwargs.get('lockTimeout', 900),
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
      value = self.client.get(keys)
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
