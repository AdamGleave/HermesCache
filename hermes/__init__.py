'''
@author: saaj
'''


import types
import hashlib
import functools
import os
import binascii

try:
  import cPickle as pickle
except ImportError:
  import pickle

from .backend import AbstractBackend


__all__ = 'Hermes', 'Mangler'


class Mangler(object):
  '''Key manager responsible for creating keys, hashing and serialization'''
  
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
    if isinstance(fn, types.MethodType):
      result.extend([fn.__self__.__class__.__name__, fn.__name__])
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
    hash = binascii.hexlify(os.urandom(4)).decode('ascii')
    return {key : self.hash(u':'.join((key, hash)).encode('utf8')) for key in tagKeys}

  def hashTags(self, tagMap):
    values = tuple(zip(*sorted(tagMap.items())))[1] # sorted by key dict values
    return self.hash(u':'.join(values).encode('utf8'))
  
  def nameLock(self, entryKey):
    parts = entryKey.split(':')
    if parts[0] == self.prefix:
      entryKey = ':'.join(parts[2:]) 
    return ':'.join([self.prefix, 'lock', entryKey])


class Hermes(object):
  '''Cache facade. Usage: 
    
      import hermes.backend.redis
    
      cache = hermes.Hermes(hermes.backend.redis.Backend, ttl = 600, host = 'localhost', db = 1)
          
          
      @cache
      def foo(a, b):
        return a * b
      
      class Example:
            
        @cache(tags = ('math', 'power'), ttl = 1200)
        def bar(self, a, b):
          return a ** b
          
        @cache(tags = ('math', 'avg'), key = lambda fn, *args, **kwargs: 'avg:{0}:{1}'.format(*args))
        def baz(self, a, b):
          return (a + b) / 2.0
  
            
      print(foo(2, 333))
      
      example = Example()
      print(example.bar(2, 10))
      print(example.baz(2, 10))
          
      foo.invalidate(2, 333)
      example.bar.invalidate(2, 10)
      example.baz.invalidate(2, 10)
          
      cache.clean(['math']) # invalidate entries tagged 'math'
      cache.clean()         # flush cache
  ''' 
  
  backend = None
  '''Cache backend'''
  
  mangler = None
  '''Key manager responsible for creating keys, hashing and serialization'''
  
  ttl = 3600
  '''Default cache entry Time To Live'''
  
  
  def __init__(self, backendClass = AbstractBackend, manglerClass = Mangler, **kwargs):
    '''Initialises the cache decorator factory. 
      
    Positional arguments are backend class and mangler class. If omitted noop-backend
    and built-in mangler will be be used.
    
    Keyword arguments comprise of ``ttl`` and backend parameters.
    '''
    
    self.ttl = kwargs.pop('ttl', self.ttl)
    
    assert issubclass(manglerClass, Mangler)
    self.mangler = manglerClass()
    
    assert issubclass(backendClass, AbstractBackend)
    self.backend = backendClass(self.mangler, **kwargs)

  def __call__(self, *args, **kwargs):
    '''Decorator that caches method or function result. The following key arguments are optional:
    
      :key:   Lambda that provides custom key, otherwise ``Mangler.nameEntry`` is used.
      :ttl:   Seconds until entry expiration, otherwise instance default is used.
      :tags:  Cache entry tag list.
      
    ``@cache`` decoration is supported as well as 
    ``@cache(ttl = 7200, tags = ('tag1', 'tag2'), key = lambda fn, *args, **kwargs: 'mykey')``.
    '''
    
    if args and isinstance(args[0], (types.FunctionType, types.MethodType)):
      # @cache
      return Cached(self.backend, self.mangler, self.ttl, args[0])
    else:
      # @cache()
      return lambda fn: Cached(self.backend, self.mangler, kwargs.pop('ttl', self.ttl), fn, **kwargs)
    
  def clean(self, tags = None):
    '''If tags argument is omitted flushes all entries, otherwise removes provided tag entries'''
    
    if tags:
      self.backend.remove(map(self.mangler.nameTag, tags))
    else:
      self.backend.clean()


class Cached(object):
  '''A wrapper for cached function or method'''
  
  _backend = None
  '''Cache backend'''
  
  _mangler = None
  '''Key manager responsible for creating keys, hashing and serializing values'''
  
  _callable = None
  '''The decorated callable, stays ``types.FunctionType`` if a function is decorated, 
  otherwise it is transformed to ``types.MethodType`` on the instance clone by descriptor 
  protocol implementation.
  '''
  
  _ttl = None
  '''Cache entry Time To Live for decorated callable'''
  
  _keyFunc  = None
  '''Key creation function'''
  
  _tags = None
  '''Cache entry tags for decorated callable'''
  
  
  def __init__(self, backend, mangler, ttl, callable, **kwargs):
    self._backend  = backend
    self._mangler  = mangler
    self._callable = callable
    self._ttl      = ttl
    self._keyFunc  = kwargs.get('key', self._mangler.nameEntry)
    self._tags     = kwargs.get('tags', None)
    # preserve ``__name__``, ``__doc__``, etc
    functools.update_wrapper(self, callable)
  
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
      namedTags   = tuple(map(self._mangler.nameTag, self._tags))
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
          value = self._callable(*args, **kwargs)
          self._save(key, value)
    return value
  
  def __get__(self, instance, type):
    '''Implements non-data descriptor protocol.
    
    The invocation happens only when instance method is decorated, so we can distinguish 
    between decorated ``types.MethodType`` and ``types.FunctionType``. Python class 
    declaration mechanics prevent a decorator from having awareness of the class type, as 
    the function is received by the decorator before it becomes an instance method.
    
    How it works::
     
      cache = hermes.Hermes()
      
      class Model:
      
        @cache
        def calc(self):
          return 42 
      
      m = Model()
      m.calc
      
    Last attribute access results in the call, ``calc.__get__(m, Model)``, where 
    ``calc`` is instance of ``hermes.Cached`` which decorates the original ``Model.calc``.
    
    Note, initially ``hermes.Cached`` is created on decoration per class method, when class 
    type is created by the interpreter, and is shared among all instances. Later, on attribute 
    access, a copy is returned with bound ``_callable``, just like ordinary Python method 
    descriptor works.    
    
    For more details, http://docs.python.org/2/howto/descriptor.html#descriptor-protocol.
    '''
    
    if not isinstance(self._callable, types.MethodType):
      methodCached          = object.__new__(Cached)
      methodCached.__dict__ = self.__dict__.copy()
      try:
        methodCached._callable = types.MethodType(self._callable, instance, type)
      except TypeError:
        # python3 compatibility
        methodCached._callable = types.MethodType(self._callable, instance)
        
      return methodCached
    
    return self

