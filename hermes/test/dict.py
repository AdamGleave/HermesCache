'''
@author: saaj
'''


import hermes.test as test
import hermes.backend.dict


cache = hermes.Hermes(hermes.backend.dict.Dict()) 


class TestDict(test.TestCase):
  
  _calls = None
  
  
  def setUp(self):
    self._calls = 0
    self.testee = cache
    
    self.testee.clean()
  
  @cache
  def bar(self, a, b):
    self._calls += 1
    return '{0}+{1}'.format(a, b)[::-1]
  
  @cache(tags = ('rock', 'tree'))
  def baz(self, a, b):
    self._calls += 1
    return '{0}-{1}'.format(a, b)[::-2]
  
  def testBasic(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({'cache:entry:TestDict:bar:109cc9a8853ebcb1' : 'ateb+ahpla'}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({'cache:entry:TestDict:bar:109cc9a8853ebcb1' : 'ateb+ahpla'}, cache._backend.cache)
    
  def testTagged(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache._backend.cache)
    
    self.assertEqual('ae-hl', self.baz('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({
      'cache:entry:TestDict:baz:109cc9a8853ebcb1:94ec8f95f633c623' : 'ae-hl',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
    self.assertEqual('ae-hl', self.baz('alpha', 'beta'))
    self.assertEqual(1,  self._calls)
    self.assertEqual({
      'cache:entry:TestDict:baz:109cc9a8853ebcb1:94ec8f95f633c623' : 'ae-hl',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
  def testFunction(self):
    @cache
    def foo(a, b):
      return '{0}+{1}'.format(a, b)[::-1]
    
    
    self.assertEqual({}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, cache._backend.cache)
    
  def testClean(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual('aldamg',     self.baz('gamma', 'delta'))
    self.assertEqual(2,  self._calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self._calls)
    self.assertEqual({}, cache._backend.cache)
    
  def testCleanTagged(self):
    self.assertEqual(0,  self._calls)
    self.assertEqual({}, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual('aldamg',     self.baz('gamma', 'delta'))
    self.assertEqual(2,            self._calls)
    self.assertEqual({
      'cache:entry:TestDict:bar:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:TestDict:baz:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
    self.testee.clean(('rock',))
    self.assertEqual({
      'cache:entry:TestDict:bar:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:TestDict:baz:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual('aldamg',     self.baz('gamma', 'delta'))
    self.assertEqual(3,            self._calls)
    self.assertEqual({
      'cache:entry:TestDict:bar:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:TestDict:baz:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual({
      'cache:entry:TestDict:bar:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:TestDict:baz:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg'
    }, cache._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.bar('alpha', 'beta'))
    self.assertEqual('aldamg',     self.baz('gamma', 'delta'))
    self.assertEqual(4,            self._calls)
    self.assertEqual({
      'cache:entry:TestDict:bar:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:TestDict:baz:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, cache._backend.cache)
    
    self.testee.clean()
    
    self.assertEqual(4, self._calls)
    self.assertEqual({}, cache._backend.cache)
