'''
@author: saaj
'''


import time
import threading

try:
  import pylibmc as memcache
except ImportError:
  import memcache
  
from . import AbstractBackend, AbstractLock


__all__ = 'Lock', 'Backend'


class Lock(AbstractLock):
  '''Key-aware distrubuted lock'''
  
  client = None
  '''Memcached client'''
  
  timeout = 900
  '''Maximum TTL of lock, can be up to 30 days, 
  otherwise memcached will treated it as a unix timestamp of an exact date'''
  
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
      if self.client.add(self.key, 'locked', self.timeout):
        return True
      elif not wait:
        return False
      else:
        time.sleep(self.sleep)

  def release(self):
    self.client.delete(self.key)


class Backend(AbstractBackend):
  '''Memcached backend implementation'''
  
  _local = None
  '''Thread-local data'''
  
  _options = None
  '''Client options'''
  
  
  def __init__(self, mangler, **kwargs):
    self.mangler  = mangler
    self._options = kwargs
    self._local   = threading.local()
  
  @property
  def client(self):
    '''Thread-mapped memcached client accessor'''
    
    if not hasattr(self._local, 'client'):
      self._local.client = memcache.Client(self._options.get('servers', ['localhost:11211']))
      
    return self._local.client
  
  def lock(self, key):
    return Lock(self.mangler.nameLock(key), self.client, **self._options)
  
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
      # python3 pylibmc returns byte keys
      return {
        k.decode() if isinstance(k, bytes) else k : self.mangler.loads(v) 
        for k, v in self.client.get_multi(tuple(keys)).items()
      }
  
  def remove(self, keys):
    if self._isScalar(keys):
      keys = (keys,)
      
    self.client.delete_multi(keys)

  def clean(self):
    self.client.flush_all()

