'''
@author: saaj
'''


import time

try:
  import pylibmc as memcache
except ImportError:
  import memcache
  
from . import AbstractBackend, AbstractLock


class Lock(AbstractLock):
  '''Key-aware distrubuted lock'''
  
  client = None
  '''Memcached client'''
  
  timeout = 900
  '''Maximum TTL of lock'''
  
  sleep = 0.1
  '''Amount of time to sleep per ``while True`` iteration when waiting'''
  
  
  def __init__(self, mangler, client, **kwargs):
    super(Lock, self).__init__(mangler)
    
    self.timeout = kwargs.get('lockTimeout', self.timeout)
    self.sleep   = kwargs.get('lockSleep', self.sleep)
    self.client  = client

  def acquire(self, wait = True):
    while True:
      if self.client.add(str(self.key), 1):
        return True
      elif not wait:
        return False
      else:
        time.sleep(self.sleep)

  def release(self):
    self.client.delete(str(self.key))


class Backend(AbstractBackend):
  '''Redis backend implementation'''
  
  client = None
  '''Redis client'''
  
  
  def __init__(self, mangler, **kwargs):
    super(Backend, self).__init__(mangler)
    
    self.client = memcache.Client(kwargs.pop('servers', ['localhost:11211']))
    self.lock   = Lock(self.mangler, self.client, **kwargs)
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    if not mapping:
      mapping = {key : value}
    mapping = {k : self.mangler.dumps(v) for k, v in mapping.items()}
    
    self.client.set_multi(mapping, ttl if ttl is not None else 0)
      
  def load(self, keys):
    if self._isScalar(keys):
      value = self.client.get(keys)
      if value is not None:
        value = self.mangler.loads(value)
      return value
    else:
      return {k : self.mangler.loads(v) for k, v in self.client.get_multi(keys).items()}
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    self.client.delete_multi(keys)

  def clean(self):
    self.client.flush_all()
