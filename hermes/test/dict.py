'''
@author: saaj
'''


import threading
import time
import json

import hermes.test as test
import hermes.backend.dict


class TestDict(test.TestCase):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.dict.Backend, ttl = 360) 
    self.fixture = test.createFixture(self.testee) 
    
    self.testee.clean()
  
  def testSimple(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'cache:entry:Fixture:simple:109cc9a8853ebcb1' : 'ateb+ahpla'
      }, self.testee.backend.dump())
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual({}, self.testee.backend.dump())

    
    self.assertEqual(1,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    expected = "])]'ammag'[(tes[+}]'ateb'[ :'ahpla'{"
    for _ in range(4):
      self.assertEqual(expected, self.fixture.simple({'alpha' : ['beta']}, [{'gamma'}]))
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual({
        'cache:entry:Fixture:simple:1791fb72b0c00b29' : expected
      }, self.testee.backend.dump())
    
    self.fixture.simple.invalidate({'alpha' : ['beta']}, [{'gamma'}])
    self.assertEqual({}, self.testee.backend.dump())
    
  def testTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(3, len(cache))
      self.assertEqual(16, len(cache.pop('cache:tag:rock')))
      self.assertEqual(16, len(cache.pop('cache:tag:tree')))
      
      expected = 'cache:entry:Fixture:tagged:109cc9a8853ebcb1'
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('ae-hl', cache.values()[0])
    
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    
    cache = self.testee.backend.dump()
    self.assertEqual(2, len(cache))
    rockTag = cache.get('cache:tag:rock')
    treeTag = cache.get('cache:tag:tree')
    self.assertNotEqual(rockTag, treeTag)
    self.assertEqual(16, len(rockTag))
    self.assertEqual(16, len(treeTag))
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(3, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(5,  len(cache))
      self.assertEqual(rockTag, cache.get('cache:tag:rock'))
      self.assertEqual(treeTag, cache.get('cache:tag:tree'))
      self.assertEqual(16, len(cache.get('cache:tag:ice')))
      
    self.testee.clean(['rock'])
    
    cache = self.testee.backend.dump()
    self.assertEqual(4, len(cache))
    self.assertTrue('cache:tag:rock' not in cache)
    iceTag = cache.get('cache:tag:ice')
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(5, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(7,  len(cache), 'has new and old entries for tagged and tagged 2 + 3 tags')
      self.assertEqual(treeTag, cache.get('cache:tag:tree'))
      self.assertEqual(iceTag,  cache.get('cache:tag:ice'))
      self.assertEqual(16, len(cache.get('cache:tag:rock')))
      self.assertNotEqual(rockTag, cache.get('cache:tag:rock'))
    
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
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      self.assertEqual(1, counter['foo'])
      self.assertEqual({'cache:entry:foo:109cc9a8853ebcb1' : 'ateb+ahpla'}, self.testee.backend.dump())
    
    foo.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({}, self.testee.backend.dump())


    self.assertEqual(0,  counter['bar'])
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      
      cache = self.testee.backend.dump()
      self.assertEqual(3,  len(cache))
      self.assertEqual(16, len(cache.pop('cache:tag:a')))
      self.assertEqual(16, len(cache.pop('cache:tag:z')))
      
      expected = 'mk:alpha:beta'
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('apabt', cache.values()[0])
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1, counter['foo'])
    
    cache = self.testee.backend.dump()
    self.assertEqual(2,  len(cache))
    self.assertEqual(16, len(cache.pop('cache:tag:a')))
    self.assertEqual(16, len(cache.pop('cache:tag:z')))

  def testKey(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(3,  len(cache))
      self.assertEqual(16, len(cache.pop('cache:tag:ash')))
      self.assertEqual(16, len(cache.pop('cache:tag:stone')))
      
      expected = 'mykey:alpha:beta'
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('apabt', cache.values()[0])
    
    self.fixture.key.invalidate('alpha', 'beta')
    
    cache = self.testee.backend.dump()
    self.assertEqual(2,  len(cache))
    self.assertEqual(16, len(cache.pop('cache:tag:ash')))
    self.assertEqual(16, len(cache.pop('cache:tag:stone')))
    
  def testAll(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(3, len(cache))
      self.assertEqual(16, len(cache.pop('cache:tag:a')))
      self.assertEqual(16, len(cache.pop('cache:tag:z')))
      
      expected = "mk:{'alpha':1}:['beta']"
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, cache.values()[0])
    
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    
    cache = self.testee.backend.dump()
    self.assertEqual(2,  len(cache))
    self.assertEqual(16, len(cache.pop('cache:tag:a')))
    self.assertEqual(16, len(cache.pop('cache:tag:z')))
  
  def testClean(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
  def testCleanTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertEqual(4, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('cache:entry:Fixture:simple:109cc9a8853ebcb1'))
    self.assertEqual(16, len(cache.pop('cache:tag:rock')))
    self.assertEqual(16, len(cache.pop('cache:tag:tree')))
    
    expected = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean(('rock',))
    
    cache = self.testee.backend.dump()
    self.assertEqual(3, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('cache:entry:Fixture:simple:109cc9a8853ebcb1'))
    self.assertEqual(16, len(cache.pop('cache:tag:tree')))
    self.assertFalse('cache:tag:rock' in cache)
    
    expected = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])

    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertEqual(5, len(cache), '+1 old tagged entry')
    self.assertEqual('ateb+ahpla', cache.pop('cache:entry:Fixture:simple:109cc9a8853ebcb1'))
    self.assertEqual(16, len(cache.pop('cache:tag:rock')))
    self.assertEqual(16, len(cache.pop('cache:tag:tree')))
    
    expected = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean(('rock', 'tree'))
    
    cache = self.testee.backend.dump()
    self.assertEqual(3, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('cache:entry:Fixture:simple:109cc9a8853ebcb1'))
    self.assertFalse('cache:tag:tree' in cache)
    self.assertFalse('cache:tag:rock' in cache)
    
    expected = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertEqual(6, len(cache), '+2 old tagged entries')
    self.assertEqual('ateb+ahpla', cache.pop('cache:entry:Fixture:simple:109cc9a8853ebcb1'))
    self.assertEqual(16, len(cache.pop('cache:tag:rock')))
    self.assertEqual(16, len(cache.pop('cache:tag:tree')))
    
    expected = 'cache:entry:Fixture:tagged:57f6833d90ca8fcb'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean()
    
    self.assertEqual(4,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
  
  def testNested(self):
    self.assertEqual('beta+alpha', self.fixture.nested('alpha', 'beta'))
    self.assertEqual(2, self.fixture.calls)
    self.assertEqual({
      'cache:entry:Fixture:nested:109cc9a8853ebcb1': 'beta+alpha', 
      'cache:entry:Fixture:simple:304d56b9ab021ab2': 'ahpla+ateb'
    }, self.testee.backend.dump())
    
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
    
    cache = self.testee.backend.dump()
    self.assertEqual(16, len(cache.pop('cache:tag:a')))
    self.assertEqual(16, len(cache.pop('cache:tag:z')))
    
    self.assertEqual('mk:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('apabt', cache.values()[0])
    
    del log[:]
    self.testee.clean()
    self.testee.backend.lock = lambda k: hermes.backend.AbstractLock(k) # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 1, 'dogpile')
    
    cache = self.testee.backend.dump()
    self.assertEqual(16, len(cache.pop('cache:tag:a')))
    self.assertEqual(16, len(cache.pop('cache:tag:z')))
    
    self.assertEqual('mk:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('apabt', cache.values()[0])


class TestDictLock(test.TestCase):
  
  def setUp(self):
    self.testee = hermes.backend.dict.Lock('123')
  
  def testAcquire(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertTrue(self.testee.acquire(False)) # reintrant within one thread
      finally:
        self.testee.release()
    
  def testRelease(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertTrue(self.testee.acquire(False)) # reintrant within one thread
      finally:
        self.testee.release()
    
  def testWith(self):
    with self.testee:
      self.assertTrue(self.testee.acquire(False)) # reintrant within one thread
      
  def testConcurrent(self):
    log   = []
    check = threading.Lock()
    def target():
      with self.testee:
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
  
  def dumps(self, value):
    return json.dumps(value)
  
  def loads(self, value):
    return json.loads(value)
  

class TestDictCustomMangler(TestDict):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.dict.Backend, CustomMangler, ttl = 360) 
    self.fixture = test.createFixture(self.testee) 
    
    self.testee.clean()
  
  def testSimple(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual({
        'hermes:entry:Fixture:simple:-1830972859' : 'ateb+ahpla'
      }, self.testee.backend.dump())
    
    self.fixture.simple.invalidate('alpha', 'beta')
    self.assertEqual({}, self.testee.backend.dump())

    
    self.assertEqual(1,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    expected = "]}'atled' :'ammag'{[+}]'ateb'[ :'ahpla'{"
    for _ in range(4):
      self.assertEqual(expected, self.fixture.simple({'alpha' : ['beta']}, [{'gamma' : 'delta'}]))
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual({
        'hermes:entry:Fixture:simple:1069401124' : expected
      }, self.testee.backend.dump())
    
    self.fixture.simple.invalidate({'alpha' : ['beta']}, [{'gamma' : 'delta'}])
    self.assertEqual({}, self.testee.backend.dump())
    
  def testTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertTrue(3, len(cache))
      self.assertFalse(cache.get('hermes:tag:tree') == cache.get('hermes:tag:rock'))
      self.assertTrue(int(cache.pop('hermes:tag:rock')) != 0)
      self.assertTrue(int(cache.pop('hermes:tag:tree')) != 0)
      
      expected = 'hermes:entry:Fixture:tagged:-1830972859'
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('ae-hl', cache.values()[0])
    
    self.fixture.tagged.invalidate('alpha', 'beta')
    
    cache = self.testee.backend.dump()
    self.assertEqual(2, len(cache))
    rockTag = cache.get('hermes:tag:rock')
    treeTag = cache.get('hermes:tag:tree')
    self.assertNotEqual(rockTag, treeTag)
    self.assertTrue(int(rockTag) != 0)
    self.assertTrue(int(treeTag) != 0)
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(3, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(5,  len(cache))
      self.assertEqual(rockTag, cache.get('hermes:tag:rock'))
      self.assertEqual(treeTag, cache.get('hermes:tag:tree'))
      self.assertTrue(int(cache.get('hermes:tag:ice')) != 0)
      
    self.testee.clean(['rock'])
    
    cache = self.testee.backend.dump()
    self.assertEqual(4, len(cache))
    self.assertTrue('hermes:tag:rock' not in cache)
    iceTag = cache.get('hermes:tag:ice')
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(5, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(7,  len(cache), 'has new and old entries for tagged and tagged 2 + 3 tags')
      self.assertEqual(treeTag, cache.get('hermes:tag:tree'))
      self.assertEqual(iceTag,  cache.get('hermes:tag:ice'))
      self.assertTrue(int(cache.get('hermes:tag:rock')) != 0)
      self.assertNotEqual(rockTag, cache.get('hermes:tag:rock'))
    
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
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      self.assertEqual(1, counter['foo'])
      self.assertEqual({'hermes:entry:foo:-1830972859' : 'ateb+ahpla'}, self.testee.backend.dump())
    
    foo.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertEqual({}, self.testee.backend.dump())


    self.assertEqual(0,  counter['bar'])
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      
      cache = self.testee.backend.dump()
      self.assertTrue(cache.get('hermes:tag:a') != cache.get('hermes:tag:z'))
      self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
      self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)
      
      self.assertEqual('mk:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('apabt', cache.values()[0])
    
    bar.invalidate('alpha', 'beta')
    
    
    self.assertEqual(1,  counter['foo'])
    
    cache = self.testee.backend.dump()
    self.assertTrue(cache.get('hermes:tag:a') != cache.get('hermes:tag:z'))
    self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)

  def testKey(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertTrue(cache.get('hermes:tag:ash') != cache.get('hermes:tag:stone'))
      self.assertTrue(int(cache.pop('hermes:tag:ash')) != 0)
      self.assertTrue(int(cache.pop('hermes:tag:stone')) != 0)
      
      self.assertEqual('mykey:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual('apabt', cache.values()[0])
    
    self.fixture.key.invalidate('alpha', 'beta')
    
    cache = self.testee.backend.dump()
    self.assertTrue(cache.get('hermes:tag:ash') != cache.get('hermes:tag:stone'))
    self.assertTrue(int(cache.pop('hermes:tag:ash')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:stone')) != 0)
    
  def testAll(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    for _ in range(4):
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      
      cache = self.testee.backend.dump()
      self.assertEqual(3, len(cache))
      self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
      self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)
      
      expected = "mk:{'alpha':1}:['beta']"
      self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, cache.values()[0])
    
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    
    cache = self.testee.backend.dump()
    self.assertEqual(2, len(cache))
    self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)
  
  def testClean(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    self.testee.clean()
    
    self.assertEqual(2,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
  def testCleanTagged(self):
    self.assertEqual(0,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(2,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertTrue(4, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('hermes:entry:Fixture:simple:-1830972859'))
    self.assertFalse(cache.get('hermes:tag:tree') == cache.get('hermes:tag:rock'))
    self.assertTrue(int(cache.pop('hermes:tag:rock')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:tree')) != 0)
    
    expected = 'hermes:entry:Fixture:tagged:-594928067'
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean(('rock',))
    
    cache = self.testee.backend.dump()
    self.assertTrue(3, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('hermes:entry:Fixture:simple:-1830972859'))
    self.assertTrue(int(cache.pop('hermes:tag:tree')) != 0)
    self.assertFalse('hermes:tag:rock' in cache)
    
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])

    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertTrue(4, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('hermes:entry:Fixture:simple:-1830972859'))
    self.assertFalse(cache.get('hermes:tag:tree') == cache.get('hermes:tag:rock'))
    self.assertTrue(int(cache.pop('hermes:tag:rock')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:tree')) != 0)
    
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean(('rock', 'tree'))
    
    cache = self.testee.backend.dump()
    self.assertTrue(2, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('hermes:entry:Fixture:simple:-1830972859'))
    self.assertFalse('hermes:tag:tree' in cache)
    self.assertFalse('hermes:tag:rock' in cache)
    
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    
    cache = self.testee.backend.dump()
    self.assertTrue(4, len(cache))
    self.assertEqual('ateb+ahpla', cache.pop('hermes:entry:Fixture:simple:-1830972859'))
    self.assertFalse(cache.get('hermes:tag:tree') == cache.get('hermes:tag:rock'))
    self.assertTrue(int(cache.pop('hermes:tag:rock')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:tree')) != 0)
    
    self.assertEqual(expected, ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('aldamg', cache.values()[0])
    
    
    self.testee.clean()
    
    self.assertEqual(4,  self.fixture.calls)
    self.assertEqual({}, self.testee.backend.dump())
  
  def testNested(self):
    self.assertEqual('beta+alpha', self.fixture.nested('alpha', 'beta'))
    self.assertEqual(2, self.fixture.calls)
    self.assertEqual({
      'hermes:entry:Fixture:nested:-1830972859': 'beta+alpha', 
      'hermes:entry:Fixture:simple:-1020720887': 'ahpla+ateb'
    }, self.testee.backend.dump())
    
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
    
    cache = self.testee.backend.dump()
    self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)
    
    self.assertEqual('mk:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('apabt', cache.values()[0])
    
    del log[:]
    self.testee.clean()
    self.testee.backend.lock = lambda k: hermes.backend.AbstractLock(k) # now see a dogpile 
    
    threads = map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4))
    map(threading.Thread.start, threads)
    map(threading.Thread.join,  threads)
    
    self.assertGreater(sum(log), 1, 'dogpile')
    
    cache = self.testee.backend.dump()
    self.assertTrue(int(cache.pop('hermes:tag:a')) != 0)
    self.assertTrue(int(cache.pop('hermes:tag:z')) != 0)
    
    self.assertEqual('mk:alpha:beta', ':'.join(cache.keys()[0].split(':')[:-1]))
    self.assertEqual('apabt', cache.values()[0])
