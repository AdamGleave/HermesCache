'''
@author: saaj
'''


import types
import hashlib
import functools
import os

try:
  import cPickle as pickle
except ImportError:
  import pickle

from backend import AbstractBackend


__all__ = 'Hermes', 'Mangler'


class Mangler(object):
  '''Key manager responsible for creating keys, hashing and serialzation'''
  
  prefix = 'cache'
  '''Prefix for cache and tag entries'''
  

  def hash(self, value):
    return hashlib.md5(value).hexdigest()[::2] # full md5 seems too long
  
  def dumps(self, value):
    return pickle.dumps(value, protocol = pickle.HIGHEST_PROTOCOL)
  
  def loads(self, value):
    return pickle.loads(value)
  
  def nameEntry(self, fn, *args, **kwargs):
    result = [self.prefix, 'entry']
    args   = list(args)
    if isinstance(fn, types.MethodType):
      result.extend([args.pop(0).__class__.__name__, fn.__name__])
    elif isinstance(fn, types.FunctionType):
      result.append(fn.__name__)
    else:
      raise TypeError('Fn is expected to be insance of MethodType or FunctionType')
    
    arguments = args, tuple(sorted(kwargs.items()))  
    result.append(self.hash(self.dumps(arguments))) 
    
    return ':'.join(result)

  def nameTag(self, tag):
    return u':'.join([self.prefix, 'tag', tag]) 

  def mapTags(self, tagKeys):
    return {key : self.hash(u':'.join((key, os.urandom(4).encode('hex')))) for key in tagKeys}

  def hashTags(self, tagMap):
    values = map(lambda (k, v): v, sorted(tagMap.items()))
    return self.hash(':'.join(values))
  
  def nameLock(self, entryKey):
    parts = entryKey.split(':')
    if parts[0] == self.prefix:
      entryKey = ':'.join(parts[2:]) 
    return ':'.join([self.prefix, 'lock', entryKey])


class Hermes(object):
  '''Cache facade''' 
  
  _backend = None
  '''Cache backend'''
  
  _mangler = None
  '''Key manager responsible for creating keys, hashing and serialzation'''
  
  _ttl = 3600
  '''Default cache entry Time To Live'''
  
  
  def __init__(self, backendClass = AbstractBackend, manglerClass = Mangler, **kwargs):
    '''Creates a cache decorator factory. Usage: ::
    
      import hermes.backend.redis
    
      cache = hermes.Hermes(hermes.backend.redis.Backend, ttl = 600)
      
      @cache
      def foo(a, b):
        return a * b
        
      @cache(tags = ('math', 'power'), ttl = 1200)
      def bar(a, b):
        return a ** b
        
      print foo(2, 333)
      print bar(2, 10)
      
      foo.invalidate(2, 333)
      bar.invalidate(2, 10)
      
      cache.clean(['math', 'power']) # remove tags
      cache.clean()                  # remove all
      
    Positional agruments are backend class and mangler class. If ommited noop-backend
    and built-in mangler will be be used.
    
    Keyword arguments comprise of ``ttl`` and backend parameters'''
    
    self._ttl = kwargs.pop('ttl', self._ttl)
    
    assert issubclass(manglerClass, Mangler)
    self._mangler = manglerClass()
    
    assert issubclass(backendClass, AbstractBackend)
    self._backend = backendClass(self._mangler, **kwargs)

  def __call__(self, *args, **kwargs):
    '''Decorator that caches method or function result. The following key arguments are optional:
    
      :key:   Lambda that provides custom key, otherwise ``Mangler.nameEntry`` is used.
      :ttl:   Seconds until enry expiration, otherwise instance default is used.
      :tags:  Cache entry tag list.
      
    ``@cache`` decoration is supported as well as 
    ``@cache(ttl = 7200, tags = ('tag1', 'tag2'), key = lambda fn, *args, **kwargs: 'mykey')``.'''
    
    if args and isinstance(args[0], (types.FunctionType, types.MethodType)):
      # @cache
      return Cached(self._backend, self._mangler, self._ttl, args[0])
    else:
      # @cache()
      return lambda fn: Cached(self._backend, self._mangler, kwargs.pop('ttl', self._ttl), fn, **kwargs)
    
  def clean(self, tags = None):
    '''If tags argument is omitted flushes all entries, otherwise removes provided tag entries'''
    
    if tags:
      self._backend.remove(map(self._mangler.nameTag, tags))
    else:
      self._backend.clean()


class Cached(object):
  '''A wrapper for cached function or method'''
  
  _backend = None
  '''Cache backend'''
  
  _mangler = None
  '''Key manager responsible for creating keys, hashing and serialzing values'''
  
  _fn = None
  '''This is always a decorated callable of ``types.FunctionType`` type'''
  
  _callable = None
  '''This value stays ``types.FunctionType`` if a function is decorated, otherwise it is 
  transformed to ``types.MethodType`` by descriptor protocol implementation'''
  
  _ttl = None
  '''Cache entry Time To Live for decarated callable'''
  
  _keyFunc  = None
  '''Key creation function'''
  
  _tags = None
  '''Cache entry tags for decarated callable'''
  
  
  def __init__(self, backend, mangler, ttl, fn, **kwargs):
    self._backend  = backend
    self._mangler  = mangler
    self._fn       = fn
    self._callable = fn
    self._ttl      = ttl
    self._keyFunc  = kwargs.get('key', self._mangler.nameEntry)
    self._tags     = kwargs.get('tags', None)
  
  def _load(self, key):
    if self._tags:
      tagMap = self._backend.load(map(self._mangler.nameTag, self._tags))
      if len(tagMap) != len(self._tags):
        return None
      else:
        key += ':' + self._mangler.hashTags(tagMap)
      
    return self._backend.load(key)
  
  def _save(self, key, value):
    if self._tags:
      namedTags   = map(self._mangler.nameTag, self._tags)
      tagMap      = self._backend.load(namedTags)
      missingTags = set(namedTags) - set(tagMap.keys())
      if missingTags:
        missingTagMap = self._mangler.mapTags(missingTags)
        self._backend.save(mapping = missingTagMap, ttl = None)
        tagMap.update(missingTagMap)
        assert len(self._tags) == len(tagMap) 
        
      key += ':' + self._mangler.hashTags(tagMap)
      
    return self._backend.save(key, value, ttl = self._ttl)
  
  def _remove(self, key):
    if self._tags:
      tagMap = self._backend.load(map(self._mangler.nameTag, self._tags))
      if len(tagMap) != len(self._tags):
        return
      else:
        key += ':' + self._mangler.hashTags(tagMap)
      
    self._backend.remove(key)
  
  def invalidate(self, *args, **kwargs):
    self._remove(self._keyFunc(self._callable, *args, **kwargs))
  
  def __call__(self, *args, **kwargs):
    key   = self._keyFunc(self._callable, *args, **kwargs)
    value = self._load(key)
    if value is None:
      with self._backend.lock(key):
        # it's better to read twice than lock every read
        value = self._load(key)
        if value is None:
          value = self._fn(*args, **kwargs)
          self._save(key, value)
    return value
  
  def __get__(self, instance, owner):
    '''Implements descriptor protocol'''
    
    # This happens only when instance method is decorated, so we can
    # surely distinguish between decorated ``types.MethodType`` and
    # ``types.FunctionType``. Python class declaration mechanics prevent 
    # a decorator from having awareness of the class type, as the 
    # function is received by the decorator before it becomes an 
    # instance method.
    self._callable = types.MethodType(self._fn, instance, owner)
    
    # Intance can also be calculated through self._callable.__self__, 
    # however the following is more convinient.
    result            = functools.partial(self.__call__,   instance)
    result.invalidate = functools.partial(self.invalidate, instance)
    
    return result
