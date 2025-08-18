"""Caching system for PDF extraction results."""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Represents a cached extraction result."""
    key: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    ttl: int
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create cache entry from dictionary."""
        return cls(**data)


def cache_key(operation: str, *args, **kwargs) -> str:
    """
    Generate a cache key for an operation with arguments.
    
    Args:
        operation: The operation name
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        SHA256 hash as cache key
    """
    # Create a string representation of the operation and arguments
    key_parts = [operation]
    key_parts.extend(str(arg) for arg in args)
    
    # Sort kwargs for consistent key generation
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")
    
    key_string = "|".join(key_parts)
    
    # Generate SHA256 hash
    return hashlib.sha256(key_string.encode()).hexdigest()


class CacheManager:
    """Manages caching of PDF extraction results."""
    
    def __init__(self, cache_dir: str = "/tmp/pdf_cache", ttl_seconds: int = 3600, max_entries: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.index_file = self.cache_dir / "cache_index.json"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache index
        self._index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index from file."""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception:
            # If index is corrupted, start fresh
            return {}
    
    def _save_index(self) -> None:
        """Save cache index to file."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception:
            pass  # Silently fail - caching is not critical
    
    def _get_cache_file_path(self, key: str) -> Path:
        """Get the file path for a cache entry."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        # Check if key exists in index
        if key not in self._index:
            return None
        
        index_entry = self._index[key]
        
        # Check if expired based on index
        if time.time() - index_entry.get('timestamp', 0) > self.ttl_seconds:
            self._remove_entry(key)
            return None
        
        # Load cache file
        cache_file = self._get_cache_file_path(key)
        if not cache_file.exists():
            # Cache file missing, remove from index
            self._remove_entry(key)
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_entry = CacheEntry.from_dict(cache_data)
            
            # Double-check expiration
            if cache_entry.is_expired():
                self._remove_entry(key)
                return None
            
            # Update access time in index
            self._index[key]['last_access'] = time.time()
            self._save_index()
            
            return cache_entry.data
            
        except Exception:
            # Cache file corrupted, remove entry
            self._remove_entry(key)
            return None
    
    def set(self, key: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Cache a result.
        
        Args:
            key: Cache key
            data: Data to cache
            metadata: Optional metadata about the cached data
        """
        if metadata is None:
            metadata = {}
        
        # Check cache size limit
        if len(self._index) >= self.max_entries:
            self._cleanup_old_entries()
        
        # Create cache entry
        cache_entry = CacheEntry(
            key=key,
            data=data,
            metadata=metadata,
            timestamp=time.time(),
            ttl=self.ttl_seconds
        )
        
        # Save cache file
        cache_file = self._get_cache_file_path(key)
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_entry.to_dict(), f, indent=2, default=str)
        except Exception:
            return  # Failed to save, don't update index
        
        # Update index
        self._index[key] = {
            'timestamp': cache_entry.timestamp,
            'last_access': cache_entry.timestamp,
            'metadata': metadata,
            'size': len(json.dumps(data, default=str))
        }
        self._save_index()
    
    def _remove_entry(self, key: str) -> None:
        """Remove a cache entry."""
        # Remove from index
        if key in self._index:
            del self._index[key]
            self._save_index()
        
        # Remove cache file
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass
    
    def _cleanup_old_entries(self) -> None:
        """Clean up old/expired cache entries."""
        current_time = time.time()
        keys_to_remove = []
        
        # Find expired entries
        for key, entry_info in self._index.items():
            if current_time - entry_info.get('timestamp', 0) > self.ttl_seconds:
                keys_to_remove.append(key)
        
        # If still too many entries, remove least recently accessed
        if len(self._index) - len(keys_to_remove) >= self.max_entries:
            # Sort by last access time
            sorted_entries = sorted(
                self._index.items(),
                key=lambda x: x[1].get('last_access', 0)
            )
            
            # Remove oldest entries
            needed_removals = len(self._index) - len(keys_to_remove) - self.max_entries + 100  # Remove extra for buffer
            for key, _ in sorted_entries[:needed_removals]:
                if key not in keys_to_remove:
                    keys_to_remove.append(key)
        
        # Remove identified entries
        for key in keys_to_remove:
            self._remove_entry(key)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file != self.index_file:
                try:
                    cache_file.unlink()
                except Exception:
                    pass
        
        # Clear index
        self._index = {}
        self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        total_entries = len(self._index)
        expired_count = 0
        total_size = 0
        
        for entry_info in self._index.values():
            if current_time - entry_info.get('timestamp', 0) > self.ttl_seconds:
                expired_count += 1
            total_size += entry_info.get('size', 0)
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_count,
            'valid_entries': total_entries - expired_count,
            'total_size_bytes': total_size,
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl_seconds,
            'max_entries': self.max_entries
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries and return count removed."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, entry_info in self._index.items():
            if current_time - entry_info.get('timestamp', 0) > self.ttl_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        return len(keys_to_remove)