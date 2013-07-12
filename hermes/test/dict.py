'''
@author: saaj
'''


import hermes.test as test
import hermes.backend.dict


cache = hermes.Hermes(hermes.backend.dict.Dict(), ttl = 360) 


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
  
  @cache(tags = ('rock', 'tree'), key = lambda fn, *args, **kwargs: 't:{0}:{1}'.format(*args))
  def key(self, a, b):
    self.calls += 1
    return '{0}*{1}'.format(a, b)[::2]
  
  @cache(tags = ('rock', 'tree'), key = lambda fn, *args, **kwargs: 't:{0}:{1}'.format(*args), ttl = 1200)
  def all(self, a, b):
    self.calls += 1
    return '{0}~{1}'.format(a, b)[::3]


class TestDict(test.TestCase):
  
  def setUp(self):
    self.testee  = cache
    self.fixture = Fixture() 
    
    self.testee.clean()
  
  def testSimple(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual(1, self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1' : 'ateb+ahpla'
    }, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual(1, self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1' : 'ateb+ahpla'
    }, self.testee._backend.cache)
    
  def testTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
    self.assertEqual(1,       self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:tagged:109cc9a8853ebcb1:94ec8f95f633c623' : 'ae-hl',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
    self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
    self.assertEqual(1,       self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:tagged:109cc9a8853ebcb1:94ec8f95f633c623' : 'ae-hl',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
  def testFunction(self):
    @cache
    def foo(a, b):
      return '{0}+{1}'.format(a, b)[::-1]
    
    
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.testee._backend.cache)
    
  def testClean(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
  def testCleanTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
    self.testee.clean(('rock',))
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg'
    }, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
    self.testee.clean()
    
    self.assertEqual(4,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
