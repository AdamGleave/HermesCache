'''
@author: saaj
'''


import time
import importlib

redis = importlib.import_module('redis')

from . import AbstractBackend, AbstractLock


__all__ = 'Lock', 'Backend'


class Lock(AbstractLock):
  '''Key-aware distrubuted lock'''
  
  client = None
  '''Redis client'''
  
  timeout = 900
  '''Maximum TTL of lock'''
  
  sleep = 0.1
  '''Amount of time to sleep per ``while True`` iteration when waiting'''
  
  
  def __init__(self, key, client, **kwargs):
    super(Lock, self).__init__(key)
    
    self.client = client
    
    self.sleep   = kwargs.get('lockSleep',   self.sleep)
    self.timeout = kwargs.get('lockTimeout', self.timeout)
    if self.timeout is None:
      self.timeout = 0

  def acquire(self, wait = True):
    while True:
      if self.client.setnx(self.key, 'locked'):
        self.client.expire(self.key, self.timeout)
        return True
      elif not wait:
        return False
      else:
        time.sleep(self.sleep)

  def release(self):
    self.client.delete(self.key)


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
      keys = tuple(keys) # py3 compat
      return {k : self.mangler.loads(v) for k, v in zip(keys, self.client.mget(keys)) if v is not None}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    self.client.delete(*keys)

  def clean(self):
    self.client.flushdb()

