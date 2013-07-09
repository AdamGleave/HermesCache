'''
@author: saaj
'''


import os


class Dictionary(object):
  '''Test purpose backend implementation'''
  
  
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

