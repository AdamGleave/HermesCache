'''
@author: saaj
'''


from . import AbstractBackend


class Null(AbstractBackend):
  '''Noop backend implementation. Can be used for temporary cache disabling.'''
  
  def save(self, key, value, map = None, ttl = None):
    pass
  
  def load(self, keys):
    return None
  
  def remove(self, keys):
    pass

  def clean(self):
    pass
