'''
@author: saaj
'''


import threading
import time
import pickle
import json

import hermes.test as test
import hermes.backend.dict


class TestDict(test.TestCase):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.dict.Backend, ttl = 360) 
    self.fixture = test.createFixture(self.testee) 
    
    self.testee.clean()
  
  def unpickleCache(self):
    return {k : pickle.loads(v) for k, v in self.testee._backend.cache.items()}
  
  def testSimple(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'cache:entry:Fixture:simple:109cc9a8853ebcb1' : 'ateb+ahpla'
      }, self.unpickleCache())
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual({}, self.unpickleCache())

    
    self.assertEqual(1,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    expected = "])]'ammag'[(tes[+}]'ateb'[ :'ahpla'{"
    for _ in range(4):
      self.assertEqual(expected, self.fixture.simple({'alpha' : ['beta']}, [{'gamma'}]))
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual({
        'cache:entry:Fixture:simple:1791fb72b0c00b29' : expected
      }, self.unpickleCache())
    
    self.fixture.simple.invalidate({'alpha' : ['beta']}, [{'gamma'}])
    self.assertEqual({}, self.unpickleCache())
    
  def testTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual({
        'cache:entry:Fixture:tagged:109cc9a8853ebcb1:94ec8f95f633c623' : 'ae-hl',
        'cache:tag:rock' : '913932947ddd381a',
        'cache:tag:tree' : 'ca7c89f9acb93af3'
      }, self.unpickleCache())
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    self.assertEqual({
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.unpickleCache())
    
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
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      self.assertEqual(1, counter['foo'])
      self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.unpickleCache())
    
    foo.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({}, self.unpickleCache())


    self.assertEqual(0,  counter['bar'])
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      self.assertEqual({
        'cache:tag:a' : '0c7bcfba3c9e6726',
        'cache:tag:z' : 'faee633dd7cb041d',
        'mk:alpha:beta:85642a5983f33b10' : 'apabt'
      }, self.unpickleCache())
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d'
    }, self.unpickleCache())

  def testKey(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual({
        'cache:tag:ash'   : '25f9af512cf657ae',
        'cache:tag:stone' : '080f56f33dfc865b',
        'mykey:alpha:beta:18af4f5a6e37713d' : 'apabt'
      }, self.unpickleCache())
    
    self.fixture.key.invalidate('alpha', 'beta')
    self.assertEqual({
      'cache:tag:ash'   : '25f9af512cf657ae',
      'cache:tag:stone' : '080f56f33dfc865b'
    }, self.unpickleCache())
    
  def testAll(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'cache:tag:a' : '0c7bcfba3c9e6726',
        'cache:tag:z' : 'faee633dd7cb041d',
        "mk:{'alpha': 1}:['beta']:85642a5983f33b10" : {'a': 1, 'b': {'b': 'beta'}}
      }, self.unpickleCache())
    
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    self.assertEqual({
      'cache:tag:a' : '0c7bcfba3c9e6726',
      'cache:tag:z' : 'faee633dd7cb041d'
    }, self.unpickleCache())
  
  def testClean(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
  def testCleanTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.unpickleCache())
    
    self.testee.clean(('rock',))
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.unpickleCache())
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg'
    }, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:simple:109cc9a8853ebcb1'                  : 'ateb+ahpla',
      'cache:entry:Fixture:tagged:57f6833d90ca8fcb:94ec8f95f633c623' : 'aldamg',
      'cache:tag:rock' : '913932947ddd381a',
      'cache:tag:tree' : 'ca7c89f9acb93af3'
    }, self.unpickleCache())
    
    self.testee.clean()
    
    self.assertEqual(4,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
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
    self.assertEqual({
      'mk:alpha:beta:85642a5983f33b10' : 'apabt', 
      'cache:tag:a' : '0c7bcfba3c9e6726', 
      'cache:tag:z' : 'faee633dd7cb041d'
    }, self.unpickleCache())
    
    del log[:]
    self.testee.clean()
    self.testee._backend.lock = hermes.backend.AbstractLock() # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 1, 'dogpile')
    self.assertEqual({
      'mk:alpha:beta:85642a5983f33b10': 'apabt', 
      'cache:tag:a' : '0c7bcfba3c9e6726', 
      'cache:tag:z': 'faee633dd7cb041d'
    }, self.unpickleCache())


class TestDictLock(test.TestCase):
  
  def setUp(self):
    self.testee = hermes.backend.dict.Lock()
  
  def testAcquire(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
      finally:
        self.testee.release()
    
  def testRelease(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
      finally:
        self.testee.release()
    
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


class CustomMangler(hermes.Mangler):
  
  prefix = 'hermes'
  '''Prefix for cache and tag entries'''
  

  def hash(self, value):
    return str(hash(value))
  
  def dump(self, value):
    return json.dumps(value)
  
  def load(self, value):
    return json.loads(value)
  

class TestDictCustomMangler(TestDict):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.dict.Backend, CustomMangler, ttl = 360) 
    self.fixture = test.createFixture(self.testee) 
    
    self.testee.clean()
  
  def unpickleCache(self):
    return {k : json.loads(v) for k, v in self.testee._backend.cache.items()}
  
  def testSimple(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'hermes:entry:Fixture:simple:-1830972859' : 'ateb+ahpla'
      }, self.unpickleCache())
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual({}, self.unpickleCache())

    
    self.assertEqual(1,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    expected = "]}'atled' :'ammag'{[+}]'ateb'[ :'ahpla'{"
    for _ in range(4):
      self.assertEqual(expected, self.fixture.simple({'alpha' : ['beta']}, [{'gamma' : 'delta'}]))
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual({
        'hermes:entry:Fixture:simple:1069401124' : expected
      }, self.unpickleCache())
    
    self.fixture.simple.invalidate({'alpha' : ['beta']}, [{'gamma' : 'delta'}])
    self.assertEqual({}, self.unpickleCache())
    
  def testTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual({
        'hermes:entry:Fixture:tagged:-1830972859:1557816737' : 'ae-hl',
        'hermes:tag:rock' : '337463927',
        'hermes:tag:tree' : '837616492'
      }, self.unpickleCache())
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    self.assertEqual({
      'hermes:tag:rock' : '337463927',
      'hermes:tag:tree' : '837616492'
    }, self.unpickleCache())
    
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
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      self.assertEqual(1, counter['foo'])
      self.assertEqual({'hermes:entry:foo:-1830972859' : 'ateb+ahpla'}, self.unpickleCache())
    
    foo.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({}, self.unpickleCache())


    self.assertEqual(0,  counter['bar'])
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      self.assertEqual({
        'hermes:tag:a' : '-468864544',
        'hermes:tag:z' : '-1563822213',
        'mk:alpha:beta:952232102' : 'apabt'
      }, self.unpickleCache())
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({
      'hermes:tag:a' : '-468864544',
      'hermes:tag:z' : '-1563822213',
    }, self.unpickleCache())

  def testKey(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual({
        'hermes:tag:ash'   : '-1585925413',
        'hermes:tag:stone' : '661884642',
        'mykey:alpha:beta:1594080686' : 'apabt'
      }, self.unpickleCache())
    
    self.fixture.key.invalidate('alpha', 'beta')
    self.assertEqual({
      'hermes:tag:ash'   : '-1585925413',
      'hermes:tag:stone' : '661884642'
    }, self.unpickleCache())
    
  def testAll(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    for _ in range(4):
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'hermes:tag:a' : '-468864544',
        'hermes:tag:z' : '-1563822213',
        "mk:{'alpha': 1}:['beta']:952232102" : {'a': 1, 'b': {'b': 'beta'}}
      }, self.unpickleCache())
    
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    self.assertEqual({
      'hermes:tag:a' : '-468864544',
      'hermes:tag:z' : '-1563822213',
    }, self.unpickleCache())
  
  def testClean(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
  def testCleanTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    self.assertEqual({
      'hermes:entry:Fixture:simple:-1830972859'           : 'ateb+ahpla',
      'hermes:entry:Fixture:tagged:-594928067:1557816737' : 'aldamg',
      'hermes:tag:rock' : '337463927',
      'hermes:tag:tree' : '837616492'
    }, self.unpickleCache())
    
    self.testee.clean(('rock',))
    self.assertEqual({
      'hermes:entry:Fixture:simple:-1830972859'           : 'ateb+ahpla',
      'hermes:entry:Fixture:tagged:-594928067:1557816737' : 'aldamg',
      'hermes:tag:tree' : '837616492'
    }, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    self.assertEqual({
      'hermes:entry:Fixture:simple:-1830972859'           : 'ateb+ahpla',
      'hermes:entry:Fixture:tagged:-594928067:1557816737' : 'aldamg',
      'hermes:tag:rock' : '337463927',
      'hermes:tag:tree' : '837616492'
    }, self.unpickleCache())
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual({
      'hermes:entry:Fixture:simple:-1830972859'           : 'ateb+ahpla',
      'hermes:entry:Fixture:tagged:-594928067:1557816737' : 'aldamg',
    }, self.unpickleCache())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    self.assertEqual({
      'hermes:entry:Fixture:simple:-1830972859'           : 'ateb+ahpla',
      'hermes:entry:Fixture:tagged:-594928067:1557816737' : 'aldamg',
      'hermes:tag:rock' : '337463927',
      'hermes:tag:tree' : '837616492'
    }, self.unpickleCache())
    
    self.testee.clean()
    
    self.assertEqual(4,  self.fixture.calls)
    self.assertEqual({}, self.unpickleCache())
    
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
    self.assertEqual({
      'mk:alpha:beta:952232102' : 'apabt', 
      'hermes:tag:a' : '-468864544', 
      'hermes:tag:z' : '-1563822213'
    }, self.unpickleCache())
    
    del log[:]
    self.testee.clean()
    self.testee._backend.lock = hermes.backend.AbstractLock() # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 1, 'dogpile')
    self.assertEqual({
      'mk:alpha:beta:952232102' : 'apabt', 
      'hermes:tag:a' : '-468864544', 
      'hermes:tag:z' : '-1563822213'
    }, self.unpickleCache())

