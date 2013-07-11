'''
@author: saaj
'''


import types
import os
import hashlib

from backend import AbstractBackend


class Hermes(object):
  
  _backend = None
  '''Cache backend'''
  
  _ttl = None
  '''Default cache entry Time To Live'''
  
  _serializer = None
  '''Function that searizlies a value to a string'''
  
  
  def __init__(self, backend, ttl = 3600, serializer = None):
    assert isinstance(backend, AbstractBackend)
    self._backend = backend
    
    self._ttl = ttl
    
    if not serializer:
      try:
        import cPickle as pickle
      except ImportError:
        import pickle
      self._serializer = lambda v: pickle.dumps(v, protocol = pickle.HIGHEST_PROTOCOL)
    else:
      self._serializer = serializer

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
      return Cached(self._backend, args[0], self._ttl, self._serializer)
    else:
      # @cache()
      return lambda fn: Cached(self._backend, fn, kwargs.get('ttl', self._ttl), self._serializer, **kwargs)
    
  def clean(self, tags = None):
    if tags:
      raise NotImplementedError()
    else:
      self._backend.clean()


class Cached(object):
  
  _backend    = None
  _callable   = None
  _serializer = None
  _ttl        = None
  _keyFunc    = None
  _tags       = None
  
  
  def __init__(self, backend, callable, ttl, serializer, **kwargs):
    self._backend    = backend
    self._callable   = callable
    self._ttl        = ttl
    self._serializer = serializer
    self._keyFunc    = kwargs.get('key', self._createEntryKey)
    self._tags       = kwargs.get('tags', None)
  
  def _isSelf(self, obj):
    '''Checkes whether provided object is an instance of new-style user class.  
    Because decorators in Python are operate functions before binding to classes 
    there's no other way to check whether it is ``types.MethodType`` or 
    ``types.FunctionType``.'''
    
    cls = obj.__class__
    return hasattr(cls, '__class__') and ('__dict__' in dir(cls) or hasattr(cls, '__slots__'))
  
  def _createEntryKey(self, fn, *args, **kwargs):
    result = ['cache', 'entry']
    args   = list(args)
    if self._isSelf(args[0]):
      result.extend([args.pop(0).__class__.__name__, fn.__name__])
    else:
      result.append(fn.__name__)
    
    arguments = (args, tuple(sorted(kwargs.items())))  
    result.append(hashlib.md5(self._serializer(arguments)).hexdigest()[::2]) # full md5 is too long
    
    return ':'.join(result)

  def _createTagKey(self, tag):
    return u':'.join(['cache', 'tag', tag]) 

  def _createTagHash(self, tagMap):
    tagValuesJoined = ':'.join(map(str, tagMap.values()))
    return hashlib.md5(tagValuesJoined).hexdigest()[::2] # full md5 is too long

  def _load(self, key):
    if self._tags:
      tagMap = self._backend.load(map(self._createTagKey, self._tags))
      if len(tagMap) != len(self._tags):
        return None
      else:
        key += ':' + self._createTagHash(tagMap)
      
    return self._backend.load(key)
  
  def _save(self, key, value):
    if self._tags:
      tagMap = {self._createTagKey(tag) : hash(tag) for tag in self._tags}
      self._backend.save(map = tagMap, ttl = None)
      key += ':' + self._createTagHash(tagMap)
      
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
