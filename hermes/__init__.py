'''
@author: saaj
'''


import types
import os
import hashlib

from backend import AbstractBackend


__all__ = ['Hermes']


class Hermes(object):
  
  _backend = None
  '''Cache backend'''
  
  _ttl = None
  '''Default cache entry Time To Live'''
  
  _dumps = None
  '''Function that searizlies a value to a string'''
  
  _keyer = None
  '''Key manager, responsible for making entry and tag keys'''
  
  
  def __init__(self, backend, ttl = 3600, dumps = None, keyer = None):
    assert isinstance(backend, AbstractBackend)
    self._backend = backend
    
    self._ttl = ttl
    
    self._dumps = dumps
    if not self._dumps:
      try:
        import cPickle as pickle
      except ImportError:
        import pickle
      self._dumps = lambda v: pickle.dumps(v, protocol = pickle.HIGHEST_PROTOCOL)
      
    self._keyer = keyer
    if not self._keyer:
      self._keyer = Keyer()

  def __call__(self, *args, **kwargs):
    '''Decorator that caches model method result. The following key 
    arguments are supported:
    
      :key:   Optional. Lambda that provides custom key, otherwise internal key function is used.
      :ttl:   Optional. Seconds until expiration, otherwise instance default is used.
      :tags:  Optional. Cache entry tag list.
      
    ``@cache`` decoration is supported as well as 
    ``@cache(ttl = 7200, tags = ('tag1', 'tag2'))``.'''
    
    if args and isinstance(args[0], (types.FunctionType, types.MethodType)):
      # @cache
      return Cached(self._backend, self._keyer, self._dumps, self._ttl, args[0])
    else:
      # @cache()
      ttl = kwargs.get('ttl', self._ttl)
      return lambda fn: Cached(self._backend, self._keyer, self._dumps, ttl, fn, **kwargs)
    
  def clean(self, tags = None):
    if tags:
      self._backend.remove(map(self._keyer.nameTag, tags))
    else:
      self._backend.clean()


class Keyer(object):
  
  prefix = 'cache'
  '''Prefix for cache and tag entries'''
  

  def _isSelf(self, obj):
    '''Checkes whether provided object is an instance of user class. Because decorators 
    in Python operate functions before binding to a classes there's no other way to 
    check whether it is ``types.MethodType`` or ``types.FunctionType``.'''
    
    # is old-style user class instance
    if isinstance(obj, types.InstanceType):
      return True
    
    # is new-style user class instance
    cls = obj.__class__
    if hasattr(cls, '__class__') and ('__dict__' in dir(cls) or hasattr(cls, '__slots__')):
      return True
    
    return False
  
  def hash(self, value):
    return hashlib.md5(value).hexdigest()[::2] # full md5 seems too long
  
  def nameEntry(self, fn, *args, **kwargs):
    result = [self.prefix, 'entry']
    args   = list(args)
    if self._isSelf(args[0]):
      result.extend([args.pop(0).__class__.__name__, fn.__name__])
    else:
      result.append(fn.__name__)
    
    arguments = args, tuple(sorted(kwargs.items()))  
    result.append(self.hash(self._serializer(arguments))) 
    
    return ':'.join(result)

  def nameTag(self, tag):
    return u':'.join([self.prefix, 'tag', tag]) 

  def mapTags(self, tags):
    return {self.nameTag(tag) : self.hash(tag) for tag in tags}

  def hashTags(self, tagMap):
    values = map(lambda (k, v): v, sorted(tagMap.items()))
    return self.hash(':'.join(values))


class Cached(object):
  
  _backend  = None
  _callable = None
  _keyer    = None
  _dumpFunc = None
  _ttl      = None
  _keyFunc  = None
  _tags     = None
  
  
  def __init__(self, backend, keyer, dumps, ttl, callable, **kwargs):
    self._backend  = backend
    self._keyer    = keyer
    self._callable = callable
    self._ttl      = ttl
    self._dumpFunc = dumps
    self._keyFunc  = kwargs.get('key', self._keyer.nameEntry)
    self._tags     = kwargs.get('tags', None)
  
  def _load(self, key):
    if self._tags:
      tagMap = self._backend.load(map(self._keyer.nameTag, self._tags))
      if len(tagMap) != len(self._tags):
        return None
      else:
        key += ':' + self._keyer.hashTags(tagMap)
      
    return self._backend.load(key)
  
  def _save(self, key, value):
    if self._tags:
      tagMap = self._keyer.mapTags(self._tags)
      self._backend.save(map = tagMap, ttl = None)
      key += ':' + self._keyer.hashTags(tagMap)
      
    return self._backend.save(key, value, ttl = self._ttl)
  
  def refresh(self, *args, **kwargs):
    key   = self._keyFunc(self._callable, *args, **kwargs)
    value = self._callable(*args, **kwargs)
    self._save(key, value)
    return value
  
  def __call__(self, *args, **kwargs):
    key   = self._keyFunc(self._callable, *args, **kwargs)
    value = self._load(key)
    if value is None:
      value = self._callable(*args, **kwargs)
      self._save(key, value)
    return value
