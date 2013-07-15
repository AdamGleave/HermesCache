'''
@author: saaj
'''


import threading
import time

import hermes.test as test
import hermes.backend.dict


class TestDict(test.TestCase):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.dict.Dict(), ttl = 360) 
    self.fixture = test.createFixture(self.testee) 
    
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
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual({}, self.testee._backend.cache)
    
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
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    self.assertEqual({
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.testee._backend.cache)
    
  def testFunction(self):
    counter = dict(foo = 0, bar = 0)
    
    @self.testee
    def foo(a, b):
      counter['foo'] += 1
      return '{0}+{1}'.format(a, b)[::-1]
    
    key = lambda fn, *args, **kwargs: 'mk:{0}:{1}'.format(*args)
    @self.testee(tags = ('a', 'z'), key = key, ttl = 120)
    def bar(a, b):
      counter['bar'] += 1
      return '{0}-{1}'.format(a, b)[::2]
    
    
    self.assertEqual(0,  counter['foo'])
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual(1, counter['foo'])
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.testee._backend.cache)
    
    self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
    self.assertEqual(1, counter['foo'])
    self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.testee._backend.cache)
    
    foo.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({}, self.testee._backend.cache)


    self.testee.clean()
    self.assertEqual(0,  counter['bar'])
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('apabt', bar('alpha', 'beta'))
    self.assertEqual(1,       counter['bar'])
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d',
      'mk:alpha:beta:85642a5983f33b10' : 'apabt'
    }, self.testee._backend.cache)
    
    self.assertEqual('apabt', bar('alpha', 'beta'))
    self.assertEqual(1,       counter['bar'])
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d',
      'mk:alpha:beta:85642a5983f33b10' : 'apabt'
    }, self.testee._backend.cache)
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d'
    }, self.testee._backend.cache)

  def testKey(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
    self.assertEqual(1,       self.fixture.calls)
    self.assertEqual({
      'cache:tag:ash'   : '25f9af512cf657ae',
      'cache:tag:stone' : '080f56f33dfc865b',
      'mykey:alpha:beta:18af4f5a6e37713d' : 'apabt'
    }, self.testee._backend.cache)
    
    self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
    self.assertEqual(1,       self.fixture.calls)
    self.assertEqual({
      'cache:tag:ash'   : '25f9af512cf657ae',
      'cache:tag:stone' : '080f56f33dfc865b',
      'mykey:alpha:beta:18af4f5a6e37713d' : 'apabt'
    }, self.testee._backend.cache)
    
    self.fixture.key.invalidate('alpha', 'beta')
    self.assertEqual({
      'cache:tag:ash'   : '25f9af512cf657ae',
      'cache:tag:stone' : '080f56f33dfc865b'
    }, self.testee._backend.cache)
    
  def testAll(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee._backend.cache)
    
    self.assertEqual({'a': ['alpha'], 'b': {'b': 'beta'}}, self.fixture.all('alpha', 'beta'))
    self.assertEqual(1, self.fixture.calls)
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d',
      'mk:alpha:beta:85642a5983f33b10' : {'a': ['alpha'], 'b': {'b': 'beta'}}
    }, self.testee._backend.cache)
    
    self.assertEqual({'a': ['alpha'], 'b': {'b': 'beta'}}, self.fixture.all('alpha', 'beta'))
    self.assertEqual(1, self.fixture.calls)
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d',
      'mk:alpha:beta:85642a5983f33b10' : {'a': ['alpha'], 'b': {'b': 'beta'}}
    }, self.testee._backend.cache)
    
    self.fixture.all.invalidate('alpha', 'beta')
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d'
    }, self.testee._backend.cache)
  
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
    
  def testConcurrent(self):
    log = []
    key = lambda fn, *args, **kwargs: 'mk:{0}:{1}'.format(*args)
    @self.testee(tags = ('a', 'z'), key = key, ttl = 120)
    def bar(a, b):
      log.append(1)
      time.sleep(0.01)
      return '{0}-{1}'.format(a, b)[::2]
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertEqual(1, sum(log))
    self.assertEqual({
      'mk:alpha:beta:85642a5983f33b10': 'apabt', 
      'cache:tag:a' : '0c7bcfba3c9e6726', 
      'cache:tag:z': 'faee633dd7cb041d'
    }, self.testee._backend.cache)
    
    del log[:]
    self.testee.clean()
    self.testee._backend.lock = hermes.backend.BaseLock() # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 2)
    self.assertEqual({
      'mk:alpha:beta:85642a5983f33b10': 'apabt', 
      'cache:tag:a' : '0c7bcfba3c9e6726', 
      'cache:tag:z': 'faee633dd7cb041d'
    }, self.testee._backend.cache)


class TestDictLock(test.TestCase):
  
  def setUp(self):
    self.testee = hermes.backend.dict.ThreadLock()
  
  def testAcquire(self):
    self.assertTrue(self.testee.acquire(True))
    self.assertFalse(self.testee.acquire(False))
    
    self.testee.release()
    
    self.assertTrue(self.testee.acquire(True))
    self.assertFalse(self.testee.acquire(False))
    
  def testRelease(self):
    self.assertTrue(self.testee.acquire(True))
    self.assertFalse(self.testee.acquire(False))
    
    self.testee.release()
    
    self.assertTrue(self.testee.acquire(True))
    self.assertFalse(self.testee.acquire(False))
    
  def testWith(self):
    with self.testee:
      self.assertFalse(self.testee.acquire(False))
      
  def testConcurrent(self):
    log   = []
    check = threading.Lock()
    def target():
      with self.testee(key = 123):
        log.append(check.acquire(False))
        time.sleep(0.05)
        check.release()
        time.sleep(0.05)
    
    threads = map(lambda i: threading.Thread(target = target), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertEqual([True] * 4, log)
