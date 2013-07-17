
***********
HermesCache
***********

Hermes is a Python caching library. The requirements it was designed to fulfill:
  
  * Tag-based cache invalidation,
  * Dogpile effect prvention,
  * Straightforward design,
  * Simple, at the same time, flexible decorator as end-user API,
  * Interface for implementing multiple backends.


Usage
=====

.. code-block:: python

  import hermes.backend.redis
    
  cache = hermes.Hermes(hermes.backend.redis.Backend, ttl = 600)
      
  @cache
  def foo(a, b):
    return a * b
        
  @cache(tags = ('math', 'power'), ttl = 1200)
  def bar(a, b):
    return a ** b
        
  print foo(2, 333)
  print bar(2, 10)
      
  foo.invalidate(2, 333)
  bar.invalidate(2, 10)
      
  cache.clean(['math', 'power']) # remove tags
  cache.clean()                  # remove all



Tagging cache entries
=====================

here some description


Reviewed implementations
========================

Reviewed implementations:

  * cache
  
    Pro:
      * clean end-user API
      * straightforward design
    Con:
      * no auto cache key calculation
      * no dogpile effect prevention
      * no cache entry tagging
      * fail with instance methods
  
  * dogpile.cache
    
    Pro:
      * mature
      * very well documented
      * prevents dogpile effect      
    Con:
      * no cache entry tagging
      * complicated codebase
      * not concise end-user API
  
  * cache-tagging

    Pro:
      * cache entry tagging      
    Con:
      * designed for the news website scaffolding framework
      * thus bloat is all around
       