'''
@author: saaj
'''


import unittest
import types


class TestCase(unittest.TestCase):

  testee = None


  def testMethodCoverage(self):
    if self.__class__ is TestCase:
      return

    def methods(object):
      return {
        name for (name, value) in object.__class__.__dict__.items()
        if isinstance(value, types.FunctionType) and name[0] != '_'
      }

    self.assertFalse(self.testee is None, 'Testee must be created in setUp()')

    diff = set('test' + name[0].upper() + name[1:] for name in methods(self.testee)) - methods(self)
    self.assertEqual(0, len(diff), 'Test case misses: {0}'.format(', '.join(diff)))


def createFixture(cache):
  
  class Fixture:
  
    calls = 0
    
    
    @cache
    def simple(self, a, b):
      self.calls += 1
      return '{0}+{1}'.format(a, b)[::-1]
    
    @cache(tags = ('rock', 'tree'))
    def tagged(self, a, b):
      self.calls += 1
      return '{0}-{1}'.format(a, b)[::-2]
    
    @cache(tags = ('rock', 'ice'))
    def tagged2(self, a, b):
      self.calls += 1
      return '{0}%{1}'.format(a, b)[::-2]
    
    @cache(tags = ('ash', 'stone'), key = lambda fn, *args, **kwargs: 'mykey:{0}:{1}'.format(*args[1:]))
    def key(self, a, b):
      self.calls += 1
      return '{0}*{1}'.format(a, b)[::2]
    
    @cache(tags = ('a', 'z'), key = lambda fn, *a: 'mk:{0}:{1}'.format(*a[1:]).replace(' ', ''), ttl = 1200)
    def all(self, a, b):
      self.calls += 1
      return {'a' : a['alpha'], 'b' : {'b' : b[0]}}
    
  return Fixture()


class TestReadme(unittest.TestCase):
  
  def testExample(self):
    import hermes.backend.redis

  
    cache = hermes.Hermes(hermes.backend.redis.Backend, ttl = 600, host = 'localhost', db = 1)
        
    @cache
    def foo(a, b):
      return a * b
    
    class Example:
          
      @cache(tags = ('math', 'power'), ttl = 1200)
      def bar(self, a, b):
        return a ** b
        
      @cache(tags = ('math', 'avg'), key = lambda fn, *args, **kwargs: 'avg:{0}:{1}'.format(*args[1:]))
      def baz(self, a, b):
        return (a + b) / 2.0

          
    print foo(2, 333)
    
    example = Example()
    print example.bar(2, 10)
    print example.baz(2, 10)
        
    foo.invalidate(2, 333)
    example.bar.invalidate(2, 10)
    example.baz.invalidate(2, 10)
        
    cache.clean(['math']) # invalidate entries tagged 'math'
    cache.clean()         # flush cache
    