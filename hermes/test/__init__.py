import hashlib
import random
import socket
import unittest
import datetime
import threading

try:
  import cPickle as pickle
except ImportError:
  import pickle


class TestCase(unittest.TestCase):

  testee = None
  '''HermesCache object'''

  fixture = None
  '''Object under test'''


  def _arghash(self, *args, **kwargs):
    '''Not very neat as it penetrates into an implementation detail, though otherwise it'll be
    harder to make assertion on keys, because pickled results are different on py2 and py3'''

    arguments = args, tuple(sorted(kwargs.items()))
    return hashlib.md5(
      pickle.dumps(arguments, protocol = pickle.HIGHEST_PROTOCOL)).hexdigest()[::2]


def createFixture(cache):

  class Fixture(object):

    calls = 0


    @cache
    def simple(self, a, b):
      '''Here be dragons... seriously just a docstring test'''

      self.calls += 1
      return '{0}+{1}'.format(a, b)[::-1]

    @cache
    def nested(self, a, b):
      self.calls += 1
      return self.simple(b, a)[::-1]

    @cache(tags = ('rock', 'tree'))
    def tagged(self, a, b):
      self.calls += 1
      return '{0}-{1}'.format(a, b)[::-2]

    @cache(tags = ('rock', 'ice'))
    def tagged2(self, a, b):
      self.calls += 1
      return '{0}%{1}'.format(a, b)[::-2]

    @cache(
      tags = ('ash', 'stone'), key = lambda fn, *args, **kwargs: 'mykey:{0}:{1}'.format(*args))
    def key(self, a, b):
      self.calls += 1
      return '{0}*{1}'.format(a, b)[::2]

    @cache(
      tags = ('a', 'z'), key = lambda fn, *a: 'mk:{0}:{1}'.format(*a).replace(' ', ''), ttl = 1200)
    def all(self, a, b):
      self.calls += 1
      return {'a' : a['alpha'], 'b' : {'b' : b[0]}}

  return Fixture()


def benchmark(fixture):
  try:
    # Python 2
    xrange = xrange  # @UndefinedVariable
  except NameError:
    # Python 3
    xrange = range

  args   = [(random.randint(0, 4096), random.randint(0, 4096)) for _ in xrange(1024)]
  repeat = 8192
  for method in ('simple', 'tagged'):
    print(
      '\n{0} {1} {2} '.format('-' * 10, fixture.simple._backend.__module__, method).ljust(50, '-'))
    start = datetime.datetime.now()
    for _ in xrange(repeat):
      getattr(fixture, method)(*random.choice(args))
    delta = datetime.datetime.now() - start
    print('  repeated:    {0:,}'.format(repeat))
    print('  time:        {0}'.format(delta))
    print('  call/second: {0:,.0f}'.format(repeat / delta.total_seconds()))


class FakeBackendServer:

  port = None
  '''Fake server port'''

  log = None
  '''Activity log'''

  thread = None
  '''Server connection-accepting thread'''

  closing = None
  '''Whether connection is closing'''


  def __init__(self):
    self.log = []

  def serve(self):
    self.closing = False

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', 0))
    serverSocket.listen(1)

    self.port = serverSocket.getsockname()[1]

    self.thread = threading.Thread(target = self.target, args = (serverSocket,))
    self.thread.start()

  def close(self):
    self.closing = True

    clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSock.connect(('localhost', self.port))

    clientSock.close()

    self.thread.join()

  def target(self, serverSocket):
    clientSocket, _ = serverSocket.accept()

    if not self.closing:
      self.log.append('connected')

    try:
      chunk = clientSocket.recv(1024)
      if not self.closing:
        if not chunk:
          self.log.append('closed')
        else:
          self.log.append('received {}'.format(chunk))
    finally:
      clientSocket.close()
      serverSocket.close()


class TestReadme(unittest.TestCase):

  def testUsage(self):
    import hermes.backend.redis


    cache = hermes.Hermes(hermes.backend.redis.Backend, ttl = 600, host = 'localhost', db = 1)

    @cache
    def foo(a, b):
      return a * b

    class Example:

      @cache(tags = ('math', 'power'), ttl = 1200)
      def bar(self, a, b):
        return a ** b

      @cache(tags = ('math', 'avg'), key = lambda fn, *args, **kwargs: 'avg:{0}:{1}'.format(*args))
      def baz(self, a, b):
        return (a + b) / 2.0


    print(foo(2, 333))

    example = Example()
    print(example.bar(2, 10))
    print(example.baz(2, 10))

    foo.invalidate(2, 333)
    example.bar.invalidate(2, 10)
    example.baz.invalidate(2, 10)

    cache.clean(['math']) # invalidate entries tagged 'math'
    cache.clean()         # flush cache

  def testNonTagged(self):
    import hermes.backend.dict

    cache = hermes.Hermes(hermes.backend.dict.Backend)

    @cache
    def foo(a, b):
      return a * b

    foo(2, 2)
    foo(2, 4)

    print(cache.backend.dump())
    #  {
    #    'cache:entry:foo:515d5cb1a98de31d': 8,
    #    'cache:entry:foo:a1c97600eac6febb': 4
    #  }

  def testTagged(self):
    import hermes.backend.dict

    cache = hermes.Hermes(hermes.backend.dict.Backend)

    @cache(tags = ('tag1', 'tag2'))
    def foo(a, b):
      return a * b

    foo(2, 2)

    print(cache.backend.dump())
    #  {
    #    u'cache:tag:tag1': '0674536f9eb4eb19',
    #    u'cache:tag:tag2': 'db22b5ab2e504895',
    #    'cache:entry:foo:a1c97600eac6febb:c1da510b3d42bad6': 4
    #  }

  def testTradeoff(self):
    import hermes.backend.dict

    cache = hermes.Hermes(hermes.backend.dict.Backend)

    @cache(tags = ('tag1', 'tag2'))
    def foo(a, b):
      return a * b

    foo(2, 2)

    print(cache.backend.dump())
    #  {
    #    u'cache:tag:tag1': '047820ac777abe8a',
    #    u'cache:tag:tag2': '126365ec7175e851',
    #    'cache:entry:foo:a1c97600eac6febb:5cae80f5e7d58329': 4
    #  }

    cache.clean(['tag1'])
    foo(2, 2)

    print(cache.backend.dump())
    #  {
    #    u'cache:tag:tag1': '66336fec212def16',
    #    u'cache:tag:tag2': '126365ec7175e851',
    #    'cache:entry:foo:a1c97600eac6febb:8e7e24cf70c1f0ab': 4,
    #    'cache:entry:foo:a1c97600eac6febb:5cae80f5e7d58329': 4
    #  }

