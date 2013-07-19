
***********
HermesCache
***********

Hermes is a Python caching library. The requirements it was designed to fulfill:

  * Tag-based cache invalidation
  * Dogpile effect prevention
  * Thread-safety 
  * Straightforward design
  * Simple, at the same time, flexible decorator as end-user API
  * Interface for implementing multiple backends

Implemented backends: ``dict``, ``memcached``, ``redis``.


Usage
=====

The following demonstrates all end-user API.

.. code-block:: python

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

For advanced examples look in
`test suite <http://code.google.com/p/hermes-py/source/browse/#hg%2Fhermes%2Ftest>`_.


Tagging cache entries
=====================

First let's look how basic caching works.

.. code-block:: python

    import hermes.backend.dict
  
    cache = hermes.Hermes(hermes.backend.dict.Backend)
        
    @cache
    def foo(a, b):
      return a * b
    
    foo(2, 2)
    foo(2, 4)
    
    print cache.backend.dump() 
    #  {
    #    'cache:entry:foo:515d5cb1a98de31d': 8, 
    #    'cache:entry:foo:a1c97600eac6febb': 4
    #                            ↓
    #                      argument hash
    #  }
        
Basically we have a key-value storage with O(1) complexity for ``set``, ``get`` and ``delete``.
This means that the speed of operation is constant and irrelevant of number of items already stored.
When a callable (function or method) is cached, the key is calculated per invocation from callable
itself and passed arguments. Callable's return value is saved to the key. Next invocation we can
use the value from cache.

  *"There are only two hard problems in Computer Science: cache invalidation and naming things."* —
  Phil Karlton

So it comes in a complex application. There's a case that certain group of methods operate the same
data and it's impractical to invalidate individual entries. In particular, it often happens when a
method returns complex values, spanning multiple entities. Cache tagging gives the possibility to mark
this group of method result with a tag and invalidate at once.

Here's `the article <http://eflorenzano.com/blog/2009/03/02/tagging-cache-keys-o1-batch-invalidation/>`_
by Eric Florenzano which explains the idea. Let's look the code.

.. code-block:: python

    import hermes.backend.dict
  
    cache = hermes.Hermes(hermes.backend.dict.Backend)
        
    @cache(tags = ('tag1', 'tag2'))
    def foo(a, b):
      return a * b
    
    foo(2, 2)
    
    print cache.backend.dump() 
    #  {
    #    u'cache:tag:tag1': '0674536f9eb4eb19', 
    #    u'cache:tag:tag2': 'db22b5ab2e504895', 
    #    'cache:entry:foo:a1c97600eac6febb:c1da510b3d42bad6': 4
    #                                              ↓
    #                                           tag hash   
    #  }
 
When we want to tag a cache entry, first we need to create the tag entries. Each tag is represented
by a its own entry. Value of a tag entry is set to random value each time tag is created. Once all tags
values exist, they are joined and hashed. Tag hash is added to cache entry key.

Once we want to invalidate tagged entries we just need to remove the tag entry. Without any of tag value
tag hash was created with, it is impossible to construct the entry key so the tagged cache entries become
inaccessible thus invalidated. As usually a feature built on-top of another feature adds complexity.

Speed. All operations become O(n) where *n* is number of entry tags. However since we can
rarely need more than a few dozens of tags, practically it is still O(1). Tag entry operations are batched
so there're following implication on number of network operations:

  * ``set`` – 3x backend calls (``get`` + 2 * ``set``) in worst case. Average is expected to be 2x when
    all used tag entries are created.
  * ``get`` – 2x backend calls.
  * ``delete`` – 2x backend calls.

Memory footprint consists of: tag entries and stale cache entries. Demonstrated below.

.. code-block:: python

    import hermes.backend.dict
  
    cache = hermes.Hermes(hermes.backend.dict.Backend)
        
    @cache(tags = ('tag1', 'tag2'))
    def foo(a, b):
      return a * b
    
    foo(2, 2)
    
    print cache.backend.dump()
    #  {
    #    u'cache:tag:tag1': '047820ac777abe8a', 
    #    u'cache:tag:tag2': '126365ec7175e851', 
    #    'cache:entry:foo:a1c97600eac6febb:5cae80f5e7d58329': 4
    #  }
    
    cache.clean(['tag1'])
    foo(2, 2)
    
    print cache.backend.dump() 
    #  {
    #    u'cache:tag:tag1': '66336fec212def16',  ← recreated tag entry
    #    u'cache:tag:tag2': '126365ec7175e851', 
    #    'cache:entry:foo:a1c97600eac6febb:8e7e24cf70c1f0ab': 4,  
    #    'cache:entry:foo:a1c97600eac6febb:5cae80f5e7d58329': 4  ← garbage
    #  }


Reviewed implementations
========================

Before I wrote the library I looked through the Cheese Shop for one that fits my needs. Unfortunately
there was none, however some matched partially and were the inspiration in certain aspects:

  * `cache <http://pypi.python.org/pypi/cache/>`_

    Pro:
      * clean end-user API
      * straightforward design
    Con:
      * no auto cache key calculation
      * no dogpile effect prevention
      * no cache entry tagging
      * fail with instance methods

  * `dogpile.cache <http://pypi.python.org/pypi/dogpile.cache/>`_

    Pro:
      * mature
      * very well documented
      * prevents dogpile effect
    Con:
      * no cache entry tagging
      * complicated code-base
      * not concise end-user API

  * `cache-tagging <http://pypi.python.org/pypi/cache-tagging/>`_

    Pro:
      * cache entry tagging
    Con:
      * designed for the news website scaffolding framework
      * thus bloat is all around
