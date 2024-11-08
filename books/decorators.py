"""
This module has cache decorators for a Django REST Framework ModelViewSet.
Although the decorators are only used in the books app, they are built to be generic, so they can be reused.
By default, they use the builtin Django cache functionality and key constructors, as they are battle-tested,
have good documentation, and cover corner cases well.
"""

# ruff: noqa: ERA001

from functools import wraps

from django.conf import settings
from django.core.cache import caches
from django.utils.cache import get_cache_key
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


def _invalidate_cache_on_update(cache=None, key_prefix=None):
    """
    Decorator that invalidates the cache of a detail view when the object is updated. If no object exists, proceed as usual.
    For cache key, we use the fact that the request path is the same on both update and detail view,
    so we can use Django's key constructor and all the niceties it provides.
    This function is not meant to be used directly.
    """

    def inner(method):
        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            nonlocal cache
            if cache is None:
                cache = caches[settings.CACHE_MIDDLEWARE_ALIAS]
            if cache_key := get_cache_key(
                request, cache=cache, key_prefix=key_prefix, method="GET"
            ):
                cache.delete(cache_key)
            return method(self, request, *args, **kwargs)

        return wrapper

    return inner


# def _cache_retrieval(timeout=60 * 5, cache=None, key_prefix=None):
#     """
#     This is a method decorator that caches the result of a method call for a given timeout.
#     Django's cache_page decorator does not use the "self" argument, so we need to use a partial function to bind the "self" argument.
#     """
#     def inner(method):
#         def wrapper(self, *args, **kwargs):
#             bound_method = wraps(method)(partial(method.__get__(self, type(self))))
#             return cache_page(timeout, cache=cache, key_prefix=key_prefix)(bound_method)(*args, **kwargs)
#         return wrapper
#     return inner


def _attach_decorator_to_methods(new_method, method_names=None):
    """
    Django's method_decorator doesn't give easy access to the request object, and we need it to get the cache key.
    That is why this function is needed.
    """

    def class_decorator(cls):
        # Check if the method exists in the class, then decorate it
        for method_name in method_names:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                setattr(cls, method_name, new_method(original_method))
            else:
                raise AttributeError(f"Method '{method_name}' not found in class.")
        return cls

    return class_decorator


def viewset_cache_detail_with_reset_on_update(timeout, cache=None, key_prefix=None):
    """
    This function returns a decorator meant to be used on modelviewsets that cache the results of GET requests and invalidates the cache on PUT and PATCH requests.
    """

    def decorator(cls):
        # Decorators for PUT and PATCH requests
        cls = _attach_decorator_to_methods(
            _invalidate_cache_on_update(cache=cache, key_prefix=key_prefix),
            method_names=["update", "partial_update"],
        )(cls)
        # Decorator for GET requests. We leverage django's cache_page decorator.
        cls = method_decorator(
            cache_page(timeout=timeout, cache=cache, key_prefix=key_prefix),
            name="retrieve",
        )(cls)

        return cls  # noqa: RET504

    return decorator
