'''
@author: saaj
'''


from . import AbstractBackend


class Null(AbstractBackend):
  '''Noop backend implementation. Can be used for temporary cache disabling.'''
  
  def save(self, key = None, value = None, mapping = None, ttl = None):
    pass
  
  def load(self, keys):
    return None if self._isScalar(keys) else {} 
  
  def remove(self, keys):
    pass

  def clean(self):
    pass
