'''
@author: saaj
'''


import types
import hashlib
import cPickle as pickle
import functools

from backend import AbstractBackend


__all__ = ['Hermes']


class Hermes(object):
  '''Cache facade''' 
  
  _backend = None
  '''Cache backend'''
  
  _mangler = None
  '''Key manager responsible for creating entry and tag keys, hashing and serialzing values'''
  
  _ttl = None
  '''Default cache entry Time To Live'''
  
  
  def __init__(self, backend, ttl = 3600, mangler = None):
    assert isinstance(backend, AbstractBackend)
    self._backend = backend
    
    self._ttl = ttl
    
    self._mangler = mangler
    if not self._mangler:
      self._mangler = Mangler()

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


class Mangler(object):
  '''Key manager responsible for creating entry and tag keys, hashing and serialzing values'''
  
  prefix = 'cache'
  '''Prefix for cache and tag entries'''
  

  def hash(self, value):
    return hashlib.md5(value).hexdigest()[::2] # full md5 seems too long
  
  def dump(self, value):
    return pickle.dumps(value, protocol = pickle.HIGHEST_PROTOCOL)
  
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
    result.append(self.hash(self.dump(arguments))) 
    
    return ':'.join(result)

  def nameTag(self, tag):
    return u':'.join([self.prefix, 'tag', tag]) 

  def mapTags(self, tags):
    return {self.nameTag(tag) : self.hash(tag) for tag in tags}

  def hashTags(self, tagMap):
    values = map(lambda (k, v): v, sorted(tagMap.items()))
    return self.hash(':'.join(values))


class Cached(object):
  '''A wrapper for cached function or method'''
  
  _backend = None
  '''Cache backend'''
  
  _mangler = None
  '''Key manager responsible for creating entry and tag keys, hashing and serialzing values'''
  
  _fn = None
  '''This is always a decorated callable of ``types.FunctionType`` type'''
  
  _callable = None
  '''This value stays ``types.FunctionType`` if a function is decorated, otherwise it is transformed
  to ``types.MethodType`` by descriptor protocol implementation'''
  
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
      tagMap = self._mangler.mapTags(self._tags)
      self._backend.save(map = tagMap, ttl = None)
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
      value = self._fn(*args, **kwargs)
      self._save(key, value)
    return value
  
  def __get__(self, instance, owner):
    '''Implements descriptor protocol'''
    
    # This happens only when instance method decorated, so we can
    # surely distinguish between decorated ``types.MethodType`` and
    # ``types.FunctionType``. Python class declaration mechanics prevent 
    # a decorator from having awareness of the class type, as the 
    # function is received by the decorator before it becomes an 
    # instance method.
    self._callable = types.MethodType(self._fn, instance, owner)
    
    # Intance can also be calculated through self._callable.__self__, 
    # however I find the following way more convinient.
    result            = functools.partial(self.__call__,   instance)
    result.invalidate = functools.partial(self.invalidate, instance)
    
    return result
