'''
@author: saaj
'''


import os


class Abstract(object):
  '''Abstract backend'''
  
  
  def clean(self, mode):
    raise NotImplementedError()
  
  def _get(self, keys):
    raise NotImplementedError()
  
  def get(self, key, tags = None):
    if tags:
      tagHash = self._get(str(set(tags)))
      if tagHash:
        key += ':' + tagHash
      else:
        return None
      
    return self._get(key, None)
  
  def _set(self, key, value):
    raise NotImplementedError()
  
  def set(self, key, value, ttl = None, tags = None):
    expire = ttl or self.ttl
    
    if tags:
      tagKey  = str(set(tags))
      tagHash = self._get(tagKey, None)
      if not tagHash:
        tagHash = os.urandom(8).encode('hex')
        self.set(tagKey, tagHash, expire)
        
      key += ':' + tagHash
      
    self._set(key, value)
