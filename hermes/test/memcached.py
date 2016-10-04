'''
@author: saaj
'''


import threading
import time
import pickle
import telnetlib

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
    stats = self.testee.backend.client.get_stats()[0][1]
    try:
      # python3-memcached
      return int(stats[b'curr_items'])
    except KeyError:
      # pylibmc
      return int(stats['curr_items'])
  
  def testSimple(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())

    key = 'cache:entry:Fixture:simple:' + self._arghash('alpha', b = 'beta')
    for _ in range(4):
      self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', b = 'beta'))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual(1, self.getSize())
  
      self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(key)))
    
    self.fixture.simple.invalidate('alpha', b = 'beta')
    self.assertEqual(0, self.getSize())
    
    
    expectedPy2 = "])]'ammag'[(tes[+}]'ateb'[ :'ahpla'{"
    expectedPy3 = "]}'ammag'{[+}]'ateb'[ :'ahpla'{"
    key      = 'cache:entry:Fixture:simple:' + self._arghash({'alpha' : ['beta']}, [{'gamma'}])
    for _ in range(4):
      try: 
        self.assertEqual(expectedPy2, self.fixture.simple({'alpha' : ['beta']}, [{'gamma'}]))
      except AssertionError:
        self.assertEqual(expectedPy3, self.fixture.simple({'alpha' : ['beta']}, [{'gamma'}]))
        
      self.assertEqual(2, self.fixture.calls)
      self.assertEqual(1, self.getSize())
      
      try:
        self.assertEqual(expectedPy2, pickle.loads(self.testee.backend.client.get(key)))
      except AssertionError:
        self.assertEqual(expectedPy3, pickle.loads(self.testee.backend.client.get(key)))
    
  def testTagged(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    for _ in range(4):    
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', b = 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual(3,       self.getSize())
      
      rockTag = pickle.loads(self.testee.backend.client.get('cache:tag:rock'))
      treeTag = pickle.loads(self.testee.backend.client.get('cache:tag:tree'))
      self.assertFalse(rockTag == treeTag)
      self.assertEqual(16, len(rockTag))
      self.assertEqual(16, len(treeTag))
      
      argHash = self._arghash('alpha', b = 'beta')
      tagHash = self.testee.mangler.hashTags(dict(tree = treeTag, rock = rockTag))
      key     = 'cache:entry:Fixture:tagged:{0}:{1}'.format(argHash, tagHash)
      self.assertEqual('ae-hl', pickle.loads(self.testee.backend.client.get(key)))
    
    self.fixture.tagged.invalidate('alpha', b = 'beta')
    
    self.assertEqual(2, self.getSize())
    
    rockTag = pickle.loads(self.testee.backend.client.get('cache:tag:rock'))
    treeTag = pickle.loads(self.testee.backend.client.get('cache:tag:tree'))
    self.assertNotEqual(rockTag, treeTag)
    self.assertEqual(16, len(rockTag))
    self.assertEqual(16, len(treeTag))
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(3, self.fixture.calls)
      
      self.assertEqual(5, self.getSize())
      self.assertEqual(rockTag, pickle.loads(self.testee.backend.client.get('cache:tag:rock')))
      self.assertEqual(treeTag, pickle.loads(self.testee.backend.client.get('cache:tag:tree')))
      self.assertEqual(16, len(pickle.loads(self.testee.backend.client.get('cache:tag:ice'))))
      
    self.testee.clean(['rock'])
    
    self.assertEqual(4, self.getSize())
    self.assertIsNone(self.testee.backend.client.get('cache:tag:rock'))
    iceTag = pickle.loads(self.testee.backend.client.get('cache:tag:ice'))
    
    for _ in range(4):
      self.assertEqual('ae-hl', self.fixture.tagged('alpha', 'beta'))
      self.assertEqual('ae%hl', self.fixture.tagged2('alpha', 'beta'))
      self.assertEqual(5, self.fixture.calls)
      
      self.assertEqual(7,  self.getSize(), 'has new and old entries for tagged and tagged 2 + 3 tags')
      self.assertEqual(treeTag, pickle.loads(self.testee.backend.client.get('cache:tag:tree')))
      self.assertEqual(iceTag, pickle.loads(self.testee.backend.client.get('cache:tag:ice')))
      self.assertEqual(16, len(pickle.loads(self.testee.backend.client.get('cache:tag:rock'))))
      self.assertNotEqual(rockTag, pickle.loads(self.testee.backend.client.get('cache:tag:rock')))
    
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
    
    key = 'cache:entry:foo:' + self._arghash('alpha', 'beta')
    for _ in range(4):
      self.assertEqual('ateb+ahpla', foo('alpha', 'beta'))
      
      self.assertEqual(1, counter['foo'])
      self.assertEqual(1, self.getSize())

      self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(key)))
    
    foo.invalidate('alpha', 'beta')
    self.assertIsNone(self.testee.backend.client.get(key))
    self.assertEqual(0, self.getSize())
    
    
    self.assertEqual(0, counter['bar'])
    self.assertEqual(0, self.getSize())
    
    for _ in range(4):
      self.assertEqual('apabt', bar('alpha', 'beta'))
      self.assertEqual(1,       counter['bar'])
      self.assertEqual(3,       self.getSize())
      
      aTag = pickle.loads(self.testee.backend.client.get('cache:tag:a'))
      zTag = pickle.loads(self.testee.backend.client.get('cache:tag:z'))
      self.assertFalse(aTag == zTag)
      self.assertEqual(16, len(aTag))
      self.assertEqual(16, len(zTag))
      
      tagHash = self.testee.mangler.hashTags(dict(a = aTag, z = zTag))
      key     = 'mk:alpha:beta:' + tagHash
      self.assertEqual('apabt', pickle.loads(self.testee.backend.client.get(key)))
    
    bar.invalidate('alpha', 'beta')
    self.assertEqual(1,  counter['foo'])
    self.assertIsNone(self.testee.backend.client.get(key))
    self.assertEqual(2, self.getSize())
    
    self.assertEqual('apabt', bar('alpha', 'beta'))
    self.assertEqual(2, counter['bar'])
    self.assertEqual(3, self.getSize())
    time.sleep(2)
    self.assertIsNone(self.testee.backend.client.get(key), 'should already expire')
    self.assertEqual(2, self.getSize())
    
    self.testee.clean(('a', 'z'))

  def testKey(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    
    for _ in range(4):
      self.assertEqual('apabt', self.fixture.key('alpha', 'beta'))
      self.assertEqual(1,       self.fixture.calls)
      self.assertEqual(3,       self.getSize())
      
      ashTag   = pickle.loads(self.testee.backend.client.get('cache:tag:ash'))
      stoneTag = pickle.loads(self.testee.backend.client.get('cache:tag:stone'))
      self.assertFalse(ashTag == stoneTag)
      self.assertEqual(16, len(ashTag))
      self.assertEqual(16, len(stoneTag))
      
      tagHash = self.testee.mangler.hashTags(dict(ash = ashTag, stone = stoneTag))
      key     = 'mykey:alpha:beta:' + tagHash
      self.assertEqual('apabt', pickle.loads(self.testee.backend.client.get(key)))
    
    self.fixture.key.invalidate('alpha', 'beta')
    
    self.assertIsNone(self.testee.backend.client.get(key))
    self.assertEqual(2, self.getSize())
    
    self.assertEqual(ashTag,   pickle.loads(self.testee.backend.client.get('cache:tag:ash')))
    self.assertEqual(stoneTag, pickle.loads(self.testee.backend.client.get('cache:tag:stone')))
      
    self.testee.clean(('a', 'z'))
    
  def testAll(self):
    self.assertEqual(0, self.fixture.calls)
    self.assertEqual(0, self.getSize())
    for _ in range(4):    
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, self.fixture.all({'alpha' : 1}, ['beta']))
      self.assertEqual(1, self.fixture.calls)
      self.assertEqual(3, self.getSize())
      
      aTag = pickle.loads(self.testee.backend.client.get('cache:tag:a'))
      zTag = pickle.loads(self.testee.backend.client.get('cache:tag:z'))
      self.assertFalse(aTag == zTag)
      self.assertEqual(16, len(aTag))
      self.assertEqual(16, len(zTag))
      
      tagHash = self.testee.mangler.hashTags(dict(a = aTag, z = zTag))
      key = "mk:{'alpha':1}:['beta']:" + tagHash
      self.assertEqual({'a': 1, 'b': {'b': 'beta'}}, pickle.loads(self.testee.backend.client.get(key)))
      
    self.fixture.all.invalidate({'alpha' : 1}, ['beta'])
    
    self.assertEqual(2, self.getSize())
    self.assertEqual(aTag, pickle.loads(self.testee.backend.client.get('cache:tag:a')))
    self.assertEqual(zTag, pickle.loads(self.testee.backend.client.get('cache:tag:z')))
    
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

    simpleKey = 'cache:entry:Fixture:simple:' + self._arghash('alpha', 'beta')
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(simpleKey)))
    
    rockTag = pickle.loads(self.testee.backend.client.get('cache:tag:rock'))
    treeTag = pickle.loads(self.testee.backend.client.get('cache:tag:tree'))
    self.assertFalse(rockTag == treeTag)
    self.assertEqual(16, len(rockTag))
    self.assertEqual(16, len(treeTag))
    
    argHash   = self._arghash('gamma', 'delta')
    tagHash   = self.testee.mangler.hashTags(dict(tree = treeTag, rock = rockTag))
    taggedKey = 'cache:entry:Fixture:tagged:{0}:{1}'.format(argHash, tagHash)
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    
    self.testee.clean(('rock',))
    self.assertEqual(3, self.getSize())
    
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(simpleKey)))
    
    self.assertIsNone(self.testee.backend.client.get('cache:tag:rock'))
    self.assertEqual(treeTag, pickle.loads(self.testee.backend.client.get('cache:tag:tree')))
    
    # stale still accessible, though only directly
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(3,            self.fixture.calls)
    self.assertEqual(5,            self.getSize(), '+1 old tagged entry')
    
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(simpleKey)))
    
    self.assertNotEqual(rockTag, pickle.loads(self.testee.backend.client.get('cache:tag:rock')))
    rockTag = pickle.loads(self.testee.backend.client.get('cache:tag:rock'))
    self.assertFalse(rockTag == treeTag)
    self.assertEqual(16, len(rockTag))
    self.assertEqual(treeTag, pickle.loads(self.testee.backend.client.get('cache:tag:tree')))
    
    # stale still accessible, though only directly
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    argHash   = self._arghash('gamma', 'delta')
    tagHash   = self.testee.mangler.hashTags(dict(tree = treeTag, rock = rockTag))
    taggedKey = 'cache:entry:Fixture:tagged:{0}:{1}'.format(argHash, tagHash)
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    
    self.testee.clean(('rock', 'tree'))
    self.assertEqual(3, self.getSize(), 'simaple, new tagged and old tagged')

    self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(simpleKey)))
    
    # new stale is accessible, though only directly
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    
    self.assertEqual('ateb+ahpla', self.fixture.simple('alpha', 'beta'))
    self.assertEqual('aldamg',     self.fixture.tagged('gamma', 'delta'))
    self.assertEqual(4,            self.fixture.calls)
    self.assertEqual(6,            self.getSize(), '+2 old tagged entries')
    
    self.assertEqual('ateb+ahpla', pickle.loads(self.testee.backend.client.get(simpleKey)))
    
    # new stale still accessible, though only directly
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    self.assertNotEqual(rockTag, pickle.loads(self.testee.backend.client.get('cache:tag:rock')))
    self.assertNotEqual(treeTag, pickle.loads(self.testee.backend.client.get('cache:tag:tree')))
    
    rockTag = pickle.loads(self.testee.backend.client.get('cache:tag:rock'))
    treeTag = pickle.loads(self.testee.backend.client.get('cache:tag:tree'))
    self.assertFalse(rockTag == treeTag)
    self.assertEqual(16, len(rockTag))
    self.assertEqual(16, len(treeTag))
    
    argHash   = self._arghash('gamma', 'delta')
    tagHash   = self.testee.mangler.hashTags(dict(tree = treeTag, rock = rockTag))
    taggedKey = 'cache:entry:Fixture:tagged:{0}:{1}'.format(argHash, tagHash)
    self.assertEqual('aldamg', pickle.loads(self.testee.backend.client.get(taggedKey)))
    
    
    self.testee.clean(('rock', 'tree'))
    self.testee.clean()
    self.assertEqual(0, self.getSize())
    
  def testNested(self):
    self.assertEqual('beta+alpha', self.fixture.nested('alpha', 'beta'))
    self.assertEqual(2, self.fixture.calls)
    key = 'cache:entry:Fixture:nested:' + self._arghash('alpha', 'beta')
    self.assertEqual('beta+alpha', pickle.loads(self.testee.backend.client.get(key)))
    key = 'cache:entry:Fixture:simple:' + self._arghash('beta', 'alpha')
    self.assertEqual('ahpla+ateb', pickle.loads(self.testee.backend.client.get(key)))  
    
  def testConcurrent(self):
    log = []
    key = lambda fn, *args, **kwargs: 'mk:{0}:{1}'.format(*args)
    @self.testee(tags = ('a', 'z'), key = key, ttl = 120)
    def bar(a, b):
      log.append(1)
      time.sleep(0.04)
      return '{0}-{1}'.format(a, b)[::2]
    
    threads = tuple(map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4)))
    tuple(map(threading.Thread.start, threads))
    tuple(map(threading.Thread.join,  threads))
    
    self.assertEqual(1, sum(log))
    self.assertEqual(3, self.getSize())
    
    aTag = pickle.loads(self.testee.backend.client.get('cache:tag:a'))
    zTag = pickle.loads(self.testee.backend.client.get('cache:tag:z'))
    self.assertFalse(aTag == zTag)
    self.assertEqual(16, len(aTag))
    self.assertEqual(16, len(zTag))
    
    tagHash = self.testee.mangler.hashTags(dict(a = aTag, z = zTag))
    key     = 'mk:alpha:beta:' + tagHash
    self.assertEqual('apabt', pickle.loads(self.testee.backend.client.get(key)))
    
    
    del log[:]
    self.testee.clean()
    self.testee.backend.lock = lambda k: hermes.backend.AbstractLock(k) # now see a dogpile 
    
    threads = tuple(map(lambda i: threading.Thread(target = bar, args = ('alpha', 'beta')), range(4)))
    tuple(map(threading.Thread.start, threads))
    tuple(map(threading.Thread.join,  threads))
    
    self.assertGreater(sum(log), 1, 'dogpile')
    # enries may be duplicated if tags overwrite
    self.assertGreaterEqual(self.getSize(), 3)
    
    aTag = pickle.loads(self.testee.backend.client.get('cache:tag:a'))
    zTag = pickle.loads(self.testee.backend.client.get('cache:tag:z'))
    self.assertFalse(aTag == zTag)
    self.assertEqual(16, len(aTag))
    self.assertEqual(16, len(zTag))

    
    self.testee.clean(('a', 'z'))


class TestMemcachedLock(test.TestCase):
  
  def setUp(self):
    cache = hermes.Hermes(hermes.backend.memcached.Backend)
    cache.clean()
    
    # make lock instance be created with client from ``hermes.Hermes`` instance at 
    # thread context to utilize ``hermes.backend.memcached.Backend`` ``thread.local``
    self.__class__.testee = property(lambda self: hermes.backend.memcached.Lock('123', cache.backend.client)) 
  
  def testAcquire(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
        self.assertEqual('123', self.testee.key)
      finally:
        self.testee.release()

  def testRelease(self):
    for _ in range(2):
      try:
        self.assertTrue(self.testee.acquire(True))
        self.assertFalse(self.testee.acquire(False))
        self.assertEqual('123', self.testee.key)
      finally:
        self.testee.release()
    
  def testWith(self):
    with self.testee:
      self.assertFalse(self.testee.acquire(False))
      self.assertEqual('123', self.testee.key)
      
      client  = hermes.backend.memcached.Backend(hermes.Mangler()).client
      another = hermes.backend.memcached.Lock('234', client)
      with another:
        self.assertFalse(another.acquire(False))
        self.assertFalse(self.testee.acquire(False))
        self.assertEqual('234', another.key)
      
  def testConcurrent(self):
    log   = []
    check = threading.Lock()
    def target():
      with self.testee:
        log.append(check.acquire(False))
        time.sleep(0.05)
        check.release()
        time.sleep(0.05)
    
    threads = tuple(map(lambda i: threading.Thread(target = target), range(4)))
    tuple(map(threading.Thread.start, threads))
    tuple(map(threading.Thread.join,  threads))
    
    self.assertEqual([True] * 4, log)


class TestMemcachedPerformance(test.unittest.TestCase):
  
  def setUp(self):
    self.testee  = hermes.Hermes(hermes.backend.memcached.Backend, ttl = 360) 
    self.fixture = test.createFixture(self.testee)
    
  def tearDown(self):
    self.forceClean()
  
  def testPerformance(self):
    test.benchmark(self.fixture)
  
  def forceClean(self):
    '''What a poorly piece of software! Most of the issues that happen within the library
    developing are memcached issues. Most notable is that it won't flush damn keys. No matter
    how many times you call it to flush, or wait for clean state -- expired by flush call keys 
    are just stale with expiry timestamp in past. Current version is 1.4.14.
    '''
    
    telnet = telnetlib.Telnet('127.0.0.1', 11211)
    try:
      telnet.write(b'stats items\n')
      slablines = telnet.read_until(b'END').split(b'\r\n')
      keys      = set()
      for line in slablines:
        parts = line.decode().split(':')
        if len(parts) < 2:
          continue
        slab = parts[1]
        telnet.write('stats cachedump {0} 0\n'.format(slab).encode())
        cachelines = telnet.read_until(b'END').split(b'\r\n')
        for line in cachelines:
          parts = line.decode().split(' ', 3)
          if len(parts) < 2:
            continue
          keys.add(parts[1])
    finally:
      telnet.close()
    
    self.testee.backend.remove(keys)
    
