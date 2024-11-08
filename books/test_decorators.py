from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.test import APIClient

from books.decorators import (
    _attach_decorator_to_methods,
    viewset_cache_detail_with_reset_on_update,
)
from books.models import Book


@viewset_cache_detail_with_reset_on_update(timeout=60)
class CachedTestViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def retrieve(self, request, *args, **kwargs):
        return Response({"test": "data"})

    def update(self, request, *args, **kwargs):
        return Response({"updated": "data"})

    def partial_update(self, request, *args, **kwargs):
        return Response({"partial": "updated"})


class CacheDecoratorTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book_data = {
            "isbn": "9780544003415",
            "title": "The Lord of the Rings",
            "author": "J.R.R. Tolkien",
            "description": "An epic fantasy novel",
            "publication_date": "1954-07-29",
        }
        self.book = Book.objects.create(**self.book_data)
        self.url = reverse("book-detail", args=[self.book.isbn])
        cache.clear()

    def test_retrieve_is_cached(self):
        # First request
        response1 = self.client.get(self.url)
        # Second request - should hit cache
        response2 = self.client.get(self.url)

        self.assertEqual(response1.data, response2.data)
        self.assertEqual(response1.status_code, 200)

    def test_update_invalidates_cache(self):
        # First cache the GET request
        self.client.get(self.url)

        # Update request should invalidate cache
        update_data = {"title": "Updated Book", "author": "Updated Author"}
        self.client.put(self.url, update_data)

        cache_key = cache.make_key(f"views.decorators.cache.cache_page.GET.{self.url}")
        self.assertIsNone(cache.get(cache_key))

    def test_partial_update_invalidates_cache(self):
        # First cache the GET request
        self.client.get(self.url)

        # Partial update should invalidate cache
        patch_data = {"title": "Partially Updated Book"}
        self.client.patch(self.url, patch_data)

        cache_key = cache.make_key(f"views.decorators.cache.cache_page.GET.{self.url}")
        self.assertIsNone(cache.get(cache_key))

    def tearDown(self):
        cache.clear()


class AttachDecoratorTests(TestCase):
    def test_attach_decorator_raises_attribute_error_for_missing_method(self):
        class DummyClass:
            def existing_method(self):
                pass

        # Try to decorate a non-existent method
        def dummy_decorator(method):
            return method
        with self.assertRaises(AttributeError) as context:
            _attach_decorator_to_methods(
                dummy_decorator,
                method_names=["non_existent_method"]
            )(DummyClass)

        self.assertEqual(
            str(context.exception),
            "Method 'non_existent_method' not found in class."
        )
