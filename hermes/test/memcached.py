'''
@author: saaj
'''


import threading
import time
import pickle

import hermes.test as test
import hermes.backend.memcached


class TestMemcached(test.TestCase):
  
  def setUp(self):
    self.testee = hermes.Hermes(hermes.backend.memcached.Backend, ttl = 360) 
    self.fixture = test.createFixture(self.testee)
    
    self.testee.clean()
    
  def tearDown(self):
    self.testee.clean()
  
  def getSize(self):
    return int(self.testee._backend.client.get_stats()[0][1]['curr_items'])
  
  def testSimple(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())

    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual(1, self.getSize())
  
      self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual(0, self.getSize())
    
    
    expected = "])]'ammag'[(tes[+}]'ateb'[ :'ahpla'{"
    key      = 'cache:entry:Fixture:simple:1791fb72b0c00b29'
    for _ in range(4): 
      self.assertEqual(expected, self.fixture.simple({'alpha' : ['beta']}, [{'gamma'}]))
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual(1, self.getSize())
  
      self.assertEqual(expected, pickle.loads(self.testee._backend.client.get(key)))
    
  def testTagged(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    for _ in range(4):    
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual(3,       self.getSize())
      
      key = 'cache:entry:Fixture:tagged:109cc9a8853ebcb1:94ec8f95f633c623'
      self.assertEqual('ae-hl',            pickle.loads(self.testee._backend.client.get(key)))
      self.assertEqual('913932947ddd381a', pickle.loads(self.testee._backend.client.get('cache:tag:rock')))
      self.assertEqual('ca7c89f9acb93af3', pickle.loads(self.testee._backend.client.get('cache:tag:tree')))
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    self.assertIsNone(self.testee._backend.client.get(key))
    self.assertEqual(2, self.getSize())
    
  def testFunction(self):
    counter = dict(foo = 0, bar = 0)
    
    @self.testee
    def foo(a, b):
      counter['foo'] += 1
      return '{0}+{1}'.format(a, b)[::-1]
    
    key = lambda fn, *args, **kwargs: 'mk:{0}:{1}'.format(*args)
    @self.testee(tags = ('a', 'z'), key = key, ttl = 1)
    def bar(a, b):
      counter['bar'] += 1
      return '{0}-{1}'.format(a, b)[::2]
    
    
    self.assertEqual(0, counter['foo'])
    self.assertEqual(0, self.getSize())
    
    key = 'cache:entry:foo:109cc9a8853ebcb1'
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      
      self.assertEqual(1, counter['foo'])
      self.assertEqual(1, self.getSize())

      self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    
    foo.invalidate('alpha', 'beta')
    self.assertIsNone(self.testee._backend.client.get(key))
    self.assertEqual(0, self.getSize())
    
    
    self.assertEqual(0, counter['bar'])
    self.assertEqual(0, self.getSize())
    
    key = 'mk:alpha:beta:85642a5983f33b10'
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      self.assertEqual(3,       self.getSize())
      
      self.assertEqual('apabt', pickle.loads(self.testee._backend.client.get(key)))
      self.assertEqual('0c7bcfba3c9e6726', pickle.loads(self.testee._backend.client.get('cache:tag:a')))
      self.assertEqual('faee633dd7cb041d', pickle.loads(self.testee._backend.client.get('cache:tag:z')))
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertIsNone(self.testee._backend.client.get(key))
    self.assertEqual(2, self.getSize())
    
    self.assertEqual('apabt', bar('alpha', 'beta'))
    self.assertEqual(2, counter['bar'])
    self.assertEqual(3, self.getSize())
    time.sleep(1.5)
    self.assertIsNone(self.testee._backend.client.get(key), 'should already expire')
    self.assertEqual(2, self.getSize())
    
    self.testee.clean(('a', 'z'))

  def testKey(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    key = 'mykey:alpha:beta:18af4f5a6e37713d'
    for _ in range(4):    
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual(3,       self.getSize())
      
      self.assertEqual('apabt',            pickle.loads(self.testee._backend.client.get(key)))
      self.assertEqual('25f9af512cf657ae', pickle.loads(self.testee._backend.client.get('cache:tag:ash')))
      self.assertEqual('080f56f33dfc865b', pickle.loads(self.testee._backend.client.get('cache:tag:stone')))
    
    self.fixture.key.invalidate('alpha', 'beta')
    self.assertIsNone(self.testee._backend.client.get(key))
    self.assertEqual(2, self.getSize())
    self.assertEqual('25f9af512cf657ae', pickle.loads(self.testee._backend.client.get('cache:tag:ash')))
    self.assertEqual('080f56f33dfc865b', pickle.loads(self.testee._backend.client.get('cache:tag:stone')))
    
    self.testee.clean(('a', 'z'))
    
  def testAll(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    key = "mk:{'alpha':1}:['beta']:85642a5983f33b10"
    for _ in range(4):    
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual(3, self.getSize())
      
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, pickle.loads(self.testee._backend.client.get(key)))
      self.assertEqual('0c7bcfba3c9e6726', pickle.loads(self.testee._backend.client.get('cache:tag:a')))
      self.assertEqual('faee633dd7cb041d', pickle.loads(self.testee._backend.client.get('cache:tag:z')))
      
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    self.assertEqual(2, self.getSize())
    self.assertEqual('0c7bcfba3c9e6726', pickle.loads(self.testee._backend.client.get('cache:tag:a')))
    self.assertEqual('faee633dd7cb041d', pickle.loads(self.testee._backend.client.get('cache:tag:z')))
    
    self.testee.clean(('a', 'z'))
  
  def testClean(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    self.assertEqual(4,            self.getSize())
    
    self.testee.clean()
    
    self.assertEqual(2, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
  def testCleanTagged(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    self.assertEqual(4,            self.getSize())

    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    key = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623'
    self.assertEqual('aldamg', pickle.loads(self.testee._backend.client.get(key)))
    
    self.assertEqual('913932947ddd381a', pickle.loads(self.testee._backend.client.get('cache:tag:rock')))
    self.assertEqual('ca7c89f9acb93af3', pickle.loads(self.testee._backend.client.get('cache:tag:tree')))
    
    
    self.testee.clean(('rock',))
    self.assertEqual(3, self.getSize())
    
    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    key = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623'
    self.assertEqual('aldamg', pickle.loads(self.testee._backend.client.get(key)))
    
    self.assertEqual('ca7c89f9acb93af3', pickle.loads(self.testee._backend.client.get('cache:tag:tree')))
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    self.assertEqual(4,            self.getSize())
    
    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    key = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623'
    self.assertEqual('aldamg', pickle.loads(self.testee._backend.client.get(key)))
    
    self.assertEqual('913932947ddd381a', pickle.loads(self.testee._backend.client.get('cache:tag:rock')))
    self.assertEqual('ca7c89f9acb93af3', pickle.loads(self.testee._backend.client.get('cache:tag:tree')))
    
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual(2, self.getSize())

    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    key = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623'
    self.assertEqual('aldamg', pickle.loads(self.testee._backend.client.get(key)))
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    self.assertEqual(4,            self.getSize())
    
    key = 'cache:entry:Fixture:simple:109cc9a8853ebcb1'
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee._backend.client.get(key)))
    key = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623'
    self.assertEqual('aldamg', pickle.loads(self.testee._backend.client.get(key)))
    
    self.assertEqual('913932947ddd381a', pickle.loads(self.testee._backend.client.get('cache:tag:rock')))
    self.assertEqual('ca7c89f9acb93af3', pickle.loads(self.testee._backend.client.get('cache:tag:tree')))
    
    self.testee.clean()
    self.assertEqual(0, self.getSize())
    
  def testConcurrent(self):
    log = []
    key = lambda fn, *args, **kwargs: 'mk:{0}:{1}'.format(*args)
    @self.testee(tags = ('a', 'z'), key = key, ttl = 120)
    def bar(a, b):
      log.append(1)
      time.sleep(0.04)
      return '{0}-{1}'.format(a, b)[::2]
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertEqual(1, sum(log))
    
    key = 'mk:alpha:beta:85642a5983f33b10'
    self.assertEqual('apabt',            pickle.loads(self.testee._backend.client.get(key)))
    self.assertEqual('0c7bcfba3c9e6726', pickle.loads(self.testee._backend.client.get('cache:tag:a')))
    self.assertEqual('faee633dd7cb041d', pickle.loads(self.testee._backend.client.get('cache:tag:z')))
    self.assertEqual(3, self.getSize())
    
    del log[:]
    self.testee.clean()
    self.testee._backend.lock = hermes.backend.AbstractLock() # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 1, 'dogpile')
    
    key = 'mk:alpha:beta:85642a5983f33b10'
    self.assertEqual('apabt',            pickle.loads(self.testee._backend.client.get(key)))
    self.assertEqual('0c7bcfba3c9e6726', pickle.loads(self.testee._backend.client.get('cache:tag:a')))
    self.assertEqual('faee633dd7cb041d', pickle.loads(self.testee._backend.client.get('cache:tag:z')))
    self.assertEqual(3, self.getSize())
    
    self.testee.clean(('a', 'z'))


class TestMemcachedLock(test.TestCase):
  
  def setUp(self):
    cache       = hermes.Hermes(hermes.backend.memcached.Backend) 
    self.testee = hermes.backend.memcached.Lock(cache._backend.mangler, cache._backend.client)
  
  def testAcquire(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
        self.assertEqual('cache:lock:default', self.testee.key)
      finally:
        self.testee.release()

  def testRelease(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
        self.assertEqual('cache:lock:default', self.testee.key)
      finally:
        self.testee.release()
    
  def testWith(self):
    with self.testee('some:key'):
      self.assertFalse(self.testee.acquire(False))
      self.assertEqual('cache:lock:some:key', self.testee.key)
      
  def testConcurrent(self):
    log   = []
    check = threading.Lock()
    def target():
      with self.testee(key = '123'):
        log.append(check.acquire(False))
        time.sleep(0.05)
        check.release()
        time.sleep(0.05)
    
    threads = map(lambda i: threading.Thread(target = target), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertEqual([True] * 4, log)
