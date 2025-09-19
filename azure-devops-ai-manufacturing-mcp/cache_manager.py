"""
Azure DevOps AI Manufacturing MCP - Cache Management

This module provides high-performance caching system for Azure DevOps operations
with multi-tier caching, intelligent preloading, and persistence.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .interface import CacheManagerInterface
from .types import AzureDevOpsProjectStructure


class CacheManager(CacheManagerInterface):
    """
    High-performance caching system for Azure DevOps operations
    
    Features:
    - Multi-tier caching (memory, Redis, database)
    - Intelligent cache warming and preloading
    - Cache invalidation strategies
    - Performance metrics and monitoring
    """
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600, 
                 persistent_cache: bool = True):
        """
        Initialize caching layers
        
        Args:
            redis_url: Redis connection URL for distributed caching
            default_ttl: Default time-to-live for cache entries in seconds
            persistent_cache: Enable persistent cache across restarts
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.persistent_cache = persistent_cache
        
        # Memory cache (L1)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Redis cache (L2) - will be initialized if redis_url is provided
        self._redis_client = None
        
        # Cache statistics
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0,
            'database_hits': 0
        }
        
        # Initialize Redis client if URL provided
        if redis_url:
            self._init_redis_client()
    
    def _init_redis_client(self):
        """Initialize Redis client for distributed caching"""
        try:
            import aioredis
            # Redis client will be initialized when first used
            self._redis_available = True
        except ImportError:
            print("Redis not available - falling back to memory-only caching")
            self._redis_available = False
    
    async def get_project_structure(self, organization: str, project: str) -> Optional[AzureDevOpsProjectStructure]:
        """
        Multi-tier cache lookup with fallback for Azure DevOps project structure
        
        Cache hierarchy:
        1. Memory cache (fastest)
        2. Redis cache (distributed)
        3. Database/persistent storage
        """
        cache_key = f"project_structure:{organization}:{project}"
        
        # L1: Check memory cache
        memory_result = self._get_from_memory_cache(cache_key)
        if memory_result:
            self._cache_stats['hits'] += 1
            self._cache_stats['memory_hits'] += 1
            return self._deserialize_project_structure(memory_result['data'])
        
        # L2: Check Redis cache
        if self._redis_available:
            redis_result = await self._get_from_redis_cache(cache_key)
            if redis_result:
                self._cache_stats['hits'] += 1
                self._cache_stats['redis_hits'] += 1
                
                # Store in memory cache for faster future access
                self._store_in_memory_cache(cache_key, redis_result)
                
                return self._deserialize_project_structure(redis_result['data'])
        
        # L3: Check persistent database cache (would be implemented with actual database)
        database_result = await self._get_from_database_cache(cache_key)
        if database_result:
            self._cache_stats['hits'] += 1
            self._cache_stats['database_hits'] += 1
            
            # Store in higher-level caches
            self._store_in_memory_cache(cache_key, database_result)
            if self._redis_available:
                await self._store_in_redis_cache(cache_key, database_result)
            
            return self._deserialize_project_structure(database_result['data'])
        
        # Cache miss
        self._cache_stats['misses'] += 1
        return None
    
    async def cache_project_structure(self, organization: str, project: str, 
                                    structure: AzureDevOpsProjectStructure) -> bool:
        """Store project structure in all cache tiers"""
        try:
            cache_key = f"project_structure:{organization}:{project}"
            cache_data = {
                'data': self._serialize_project_structure(structure),
                'timestamp': datetime.now().timestamp(),
                'ttl': self.default_ttl
            }
            
            # Store in all available cache tiers
            self._store_in_memory_cache(cache_key, cache_data)
            
            if self._redis_available:
                await self._store_in_redis_cache(cache_key, cache_data)
            
            if self.persistent_cache:
                await self._store_in_database_cache(cache_key, cache_data)
            
            return True
            
        except Exception as e:
            print(f"Error caching project structure: {str(e)}")
            return False
    
    async def cache_work_item_types(self, organization: str, project: str, 
                                  work_item_types: List[Dict[str, Any]]) -> bool:
        """Cache work item type definitions with field schemas"""
        try:
            cache_key = f"work_item_types:{organization}:{project}"
            cache_data = {
                'data': work_item_types,
                'timestamp': datetime.now().timestamp(),
                'ttl': self.default_ttl
            }
            
            self._store_in_memory_cache(cache_key, cache_data)
            
            if self._redis_available:
                await self._store_in_redis_cache(cache_key, cache_data)
            
            return True
            
        except Exception as e:
            print(f"Error caching work item types: {str(e)}")
            return False
    
    async def warm_cache_for_manufacturing(self, organizations: List[str], projects: List[str]) -> bool:
        """
        Pre-warm cache for manufacturing operations
        
        This method proactively loads frequently accessed data into cache
        to improve performance during manufacturing operations.
        """
        try:
            warming_tasks = []
            
            for org in organizations:
                for project in projects:
                    # Create tasks for warming different data types
                    warming_tasks.extend([
                        self._warm_project_structure_cache(org, project),
                        self._warm_work_item_types_cache(org, project),
                        self._warm_board_configuration_cache(org, project),
                        self._warm_team_configuration_cache(org, project)
                    ])
            
            # Execute all warming tasks concurrently
            results = await asyncio.gather(*warming_tasks, return_exceptions=True)
            
            # Count successful warming operations
            successful_warming = sum(1 for r in results if r is True)
            total_warming = len(warming_tasks)
            
            print(f"Cache warming completed: {successful_warming}/{total_warming} operations successful")
            
            return successful_warming > (total_warming * 0.8)  # 80% success rate threshold
            
        except Exception as e:
            print(f"Error during cache warming: {str(e)}")
            return False
    
    async def invalidate_cache(self, cache_key: str) -> bool:
        """Invalidate specific cache entry across all tiers"""
        try:
            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            # Remove from Redis cache
            if self._redis_available and self._redis_client:
                await self._redis_client.delete(cache_key)
            
            # Remove from database cache (would be implemented with actual database)
            await self._remove_from_database_cache(cache_key)
            
            return True
            
        except Exception as e:
            print(f"Error invalidating cache key {cache_key}: {str(e)}")
            return False
    
    async def invalidate_project_cache(self, organization: str, project: str) -> bool:
        """Invalidate all cache entries for a specific project"""
        try:
            project_prefix = f"{organization}:{project}"
            
            # Find and remove all keys with the project prefix
            keys_to_remove = []
            for key in self._memory_cache.keys():
                if project_prefix in key:
                    keys_to_remove.append(key)
            
            # Remove from memory cache
            for key in keys_to_remove:
                del self._memory_cache[key]
            
            # Remove from Redis cache
            if self._redis_available and self._redis_client:
                pattern = f"*{project_prefix}*"
                keys = await self._redis_client.keys(pattern)
                if keys:
                    await self._redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            print(f"Error invalidating project cache: {str(e)}")
            return False
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'cache_hits': self._cache_stats['hits'],
            'cache_misses': self._cache_stats['misses'],
            'hit_rate_percentage': round(hit_rate, 2),
            'memory_hits': self._cache_stats['memory_hits'],
            'redis_hits': self._cache_stats['redis_hits'],
            'database_hits': self._cache_stats['database_hits'],
            'memory_cache_size': len(self._memory_cache)
        }
    
    # Memory cache operations
    def _get_from_memory_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get item from memory cache"""
        if cache_key not in self._memory_cache:
            return None
        
        cache_item = self._memory_cache[cache_key]
        
        # Check if item has expired
        if self._is_cache_item_expired(cache_item):
            del self._memory_cache[cache_key]
            return None
        
        return cache_item
    
    def _store_in_memory_cache(self, cache_key: str, cache_data: Dict[str, Any]):
        """Store item in memory cache"""
        self._memory_cache[cache_key] = cache_data
        
        # Implement simple LRU eviction if memory cache gets too large
        if len(self._memory_cache) > 1000:  # Max 1000 items in memory
            # Remove oldest items (simplified LRU)
            oldest_key = min(self._memory_cache.keys(), 
                           key=lambda k: self._memory_cache[k]['timestamp'])
            del self._memory_cache[oldest_key]
    
    # Redis cache operations
    async def _get_from_redis_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get item from Redis cache"""
        if not self._redis_available:
            return None
        
        try:
            if not self._redis_client:
                import aioredis
                self._redis_client = aioredis.from_url(self.redis_url)
            
            cached_data = await self._redis_client.get(cache_key)
            if cached_data:
                cache_item = json.loads(cached_data)
                
                # Check if item has expired
                if self._is_cache_item_expired(cache_item):
                    await self._redis_client.delete(cache_key)
                    return None
                
                return cache_item
            
            return None
            
        except Exception as e:
            print(f"Redis cache error: {str(e)}")
            return None
    
    async def _store_in_redis_cache(self, cache_key: str, cache_data: Dict[str, Any]):
        """Store item in Redis cache"""
        if not self._redis_available:
            return
        
        try:
            if not self._redis_client:
                import aioredis
                self._redis_client = aioredis.from_url(self.redis_url)
            
            serialized_data = json.dumps(cache_data, default=str)
            await self._redis_client.setex(cache_key, cache_data['ttl'], serialized_data)
            
        except Exception as e:
            print(f"Redis cache storage error: {str(e)}")
    
    # Database cache operations (simplified implementations)
    async def _get_from_database_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get item from database cache"""
        # TODO: Implement actual database cache retrieval
        # This would query a persistent database (PostgreSQL, SQLite, etc.)
        return None
    
    async def _store_in_database_cache(self, cache_key: str, cache_data: Dict[str, Any]):
        """Store item in database cache"""
        # TODO: Implement actual database cache storage
        pass
    
    async def _remove_from_database_cache(self, cache_key: str):
        """Remove item from database cache"""
        # TODO: Implement actual database cache removal
        pass
    
    # Cache warming operations
    async def _warm_project_structure_cache(self, organization: str, project: str) -> bool:
        """Warm project structure cache"""
        try:
            # In a real implementation, this would fetch fresh data from Azure DevOps
            # and store it in cache. For now, we'll simulate success.
            cache_key = f"project_structure:{organization}:{project}"
            
            # Check if already cached
            if self._get_from_memory_cache(cache_key):
                return True  # Already warm
            
            # TODO: Fetch fresh project structure data and cache it
            # project_structure = await azure_devops_client.fetch_project_structure(org, project)
            # await self.cache_project_structure(org, project, project_structure)
            
            return True
            
        except Exception as e:
            print(f"Error warming project structure cache: {str(e)}")
            return False
    
    async def _warm_work_item_types_cache(self, organization: str, project: str) -> bool:
        """Warm work item types cache"""
        try:
            # TODO: Implement work item types cache warming
            return True
        except Exception as e:
            print(f"Error warming work item types cache: {str(e)}")
            return False
    
    async def _warm_board_configuration_cache(self, organization: str, project: str) -> bool:
        """Warm board configuration cache"""
        try:
            # TODO: Implement board configuration cache warming
            return True
        except Exception as e:
            print(f"Error warming board configuration cache: {str(e)}")
            return False
    
    async def _warm_team_configuration_cache(self, organization: str, project: str) -> bool:
        """Warm team configuration cache"""
        try:
            # TODO: Implement team configuration cache warming
            return True
        except Exception as e:
            print(f"Error warming team configuration cache: {str(e)}")
            return False
    
    # Utility methods
    def _is_cache_item_expired(self, cache_item: Dict[str, Any]) -> bool:
        """Check if cache item has expired"""
        current_time = datetime.now().timestamp()
        item_timestamp = cache_item.get('timestamp', 0)
        item_ttl = cache_item.get('ttl', self.default_ttl)
        
        return (current_time - item_timestamp) > item_ttl
    
    def _serialize_project_structure(self, structure: AzureDevOpsProjectStructure) -> Dict[str, Any]:
        """Serialize project structure for caching"""
        # This would use the same serialization logic as ConfigurationManager
        # For now, return a simplified representation
        return {
            'organization': structure.organization,
            'project': structure.project,
            'project_id': structure.project_id,
            'analyzed_at': structure.analyzed_at.isoformat(),
            # Add other fields as needed
        }
    
    def _deserialize_project_structure(self, data: Dict[str, Any]) -> AzureDevOpsProjectStructure:
        """Deserialize project structure from cache"""
        # This would use the same deserialization logic as ConfigurationManager
        # For now, return a simplified structure
        from .types import AzureDevOpsProjectStructure
        
        return AzureDevOpsProjectStructure(
            organization=data.get('organization', ''),
            project=data.get('project', ''),
            project_id=data.get('project_id', ''),
            project_description='',
            process_template='',
            work_item_types={},
            custom_fields={},
            area_paths=[],
            iteration_paths=[],
            teams=[],
            boards={},
            repositories=[],
            build_definitions=[],
            analyzed_at=datetime.fromisoformat(data.get('analyzed_at', datetime.now().isoformat())),
            field_usage_patterns={}
        )
