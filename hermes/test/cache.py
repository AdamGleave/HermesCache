'''
@author: saaj
'''


import test
import cache


class TestCache(test.TestCase):
  
  _calls = None
  
  
  def setUp(self):
    self._calls = 0
    cache.backend.reset()
  
  @cache.cache
  def bar(self, a, b):
    self._calls += 1
    return '{0}+{1}'.format(a, b)[::-1]
  
  @cache.cache(tags = ('tree', 'rock'))
  def baz(self, a, b):
    self._calls += 1
    return '{0}-{1}'.format(a, b)[::-2]
  
  def testBasic(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache.backend.data)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({u"TestCache.bar:['alpha', 'beta']:{}" : 'ateb+ahpla'}, cache.backend.data)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({u"TestCache.bar:['alpha', 'beta']:{}" : 'ateb+ahpla'}, cache.backend.data)
    
  def testTagged(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache.backend.data)
    
    self.assertEqual('ae-hl', self.baz('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({
      u'TestCache.baz:alpha,beta:722a6251-f8b3-4171-ae62-24a92ec9f2d2': 'ae-hl',
      "set(['tree', 'rock'])" : '722a6251-f8b3-4171-ae62-24a92ec9f2d2'
    }, cache.backend.data)
    
    self.assertEqual('ae-hl', self.baz('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({u'TestCache.bar:alpha,beta' : 'ae-hl'}, cache.backend.data)
    
  def testFunction(self):
    @cache.cache
    def foo(a, b):
      return '{0}+{1}'.format(a, b)[::-1]
    
    
    self.assertEqual({}, cache.backend.data)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({u"foo:['alpha', 'beta']:{}" : 'ateb+ahpla'}, cache.backend.data)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({u"foo:['alpha', 'beta']:{}" : 'ateb+ahpla'}, cache.backend.data)
    