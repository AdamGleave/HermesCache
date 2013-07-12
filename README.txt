
***********
HermesCache
***********

Hermes is yet another Python caching library with tab-based imvalidation. The goals to achieve:
  
  * Tag-based cache invalidation,
  * Simple and flexible decorator as end-user API,
  * Interface for multiple backend,
  * Main backend is Redis.

  
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
      * big codebase
      * not concise end-user API
  
  * cache-tagging

    Pro:
      * cache entry tagging      
    Con:
      * designed for the news site scaffolding framework
      * bloated
       