from .sync_dec import SyncDjapifyDecorator
from .async_dec import AsyncDjapifyDecorator


def djapify(view_func=None, **kwargs):
   """Synchronous djapify decorator"""
   decorator = SyncDjapifyDecorator(view_func, **kwargs)
   return decorator(view_func) if view_func else decorator


def async_djapify(view_func=None, **kwargs):
   """Asynchronous djapify decorator"""
   decorator = AsyncDjapifyDecorator(view_func, **kwargs)
   return decorator(view_func) if view_func else decorator


__all__ = ['djapify', 'async_djapify']
