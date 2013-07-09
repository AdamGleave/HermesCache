'''
@author: saaj
'''


import types
import os


def isNewStyleUserClassIntance(obj):
  cls = obj.__class__
  return hasattr(cls, '__class__') and ('__dict__' in dir(cls) or hasattr(cls, '__slots__'))


def createKey(fn, *args, **kwargs):
  result = []
  args   = list(args)
  if isNewStyleUserClassIntance(args[0]):
    result.append('{0}.{1}'.format(args.pop(0).__class__.__name__, fn.__name__))
  else:
    result.append(fn.__name__)
    
  result.extend(map(unicode, (args, kwargs)))
  
  return u':'.join(result)


class DictBackend:
  '''Examplary backend implementation for a proof of concept'''
  
  
  expire = None
  data   = None
  
  
  def __init__(self, expire):
    self.expire = expire
    self.data   = {}
  
  def reset(self):
    self.data.clear()
  
  def get(self, key, tags = None):
    if tags:
      tagHash = self.get(str(set(tags)))
      if tagHash:
        key += ':' + tagHash
      else:
        return None
    return self.data.get(key, None)
  
  def set(self, key, value, expire = None, tags = None):
    expire = expire or self.expire # ignore in proof of concept
    
    if tags:
      tagKey  = str(set(tags))
      tagHash = self.get(tagKey, None)
      if not tagHash:
        tagHash = os.urandom(8).encode('hex')
        self.set(tagKey, tagHash, expire)
        
      key += ':' + tagHash
      
    self.data[key] = value

backend = DictBackend(3600)


def cache(*args, **kwargs):
  '''Decorator that caches model method result. The following key 
  arguments are supported:
  
    :key:     Optional. Lambda that provides custom key, otherwise internal key function is used.
    :expire:  Optional. Seconds until expiration, otherwise backend default is used.
    :tags:    Optional. Cache entry tag list.
    
  ``@cache`` decoration is supported as well as 
  ``@cache(expire = 7200, tags = ('tag1', 'tag2'))``.'''
  
  params = {
    'creator' : None,
    'key'     : None,    
    'expire'  : None,
    'tags'    : None
  }
  def cached(*args, **kwargs):
    actual = (params['key'] or createKey)(params['creator'], *args, **kwargs)
    value  = backend.get(actual, tags = params['tags'])
    if not value:
      value = params['creator'](*args, **kwargs)
      backend.set(actual, value, expire = params['expire'], tags = params['tags'])
    return value
  
  if args and isinstance(args[0], (types.FunctionType, types.MethodType)):
    # @cache
    params['creator'] = args[0]
    return cached
  else:
    # @cache()
    params['expire'] = kwargs.get('expire', None)
    params['tags']   = kwargs.get('tags',   None)
    def wrap(fn):
      params['creator'] = fn
      return cached
    return wrap
