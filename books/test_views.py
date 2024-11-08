import logging
from json import JSONDecodeError
from unittest.mock import patch

import httpx
from django.core.cache import cache
from django.urls import reverse
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book


class BasicCRUDTests(APITestCase):
    def setUp(self):
        self.book_data = {
            "isbn": "9780544003415",
            "title": "The Lord of the Rings",
            "author": "J.R.R. Tolkien",
            "description": "An epic fantasy novel",
            "publication_date": "1954-07-29",
        }
        self.book = Book.objects.create(**self.book_data)
        self.books_url = reverse("book-list")
        self.book_detail_url = reverse("book-detail", args=[self.book.isbn])

    def test_create_book(self):
        new_book_data = {
            "isbn": "9780547928227",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_create_missing_publication_date(self):
        new_book_data = {
            "isbn": "9780547928229",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            # 'publication_date': '1937-09-21'
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_isbn(self):
        new_book_data = {
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_isbn10(self):
        new_book_data = {
            "isbn": "123456789A",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_isbn13(self):
        new_book_data = {
            "isbn": "123456789ABCD",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_title(self):
        new_book_data = {
            "isbn": "9780547928229",
            "author": "J.R.R. Tolkien",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_author(self):
        new_book_data = {
            "isbn": "9780547928229",
            "title": "The Hobbit",
            "description": "A fantasy novel",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_description(self):
        new_book_data = {
            "isbn": "9780547928229",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "publication_date": "1937-09-21",
        }
        response = self.client.post(self.books_url, new_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_book_list(self):
        response = self.client.get(self.books_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_book_detail(self):
        response = self.client.get(self.book_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["isbn"], self.book_data["isbn"])
        self.assertEqual(response.data["title"], self.book_data["title"])

    def test_update_book_using_patch(self):
        updated_data = {
            "title": "Something completely different",
            "description": "Updated description",
        }
        response = self.client.patch(self.book_detail_url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, updated_data["title"])
        self.assertEqual(self.book.description, updated_data["description"])

    def test_update_book_using_put_same_isbn(self):
        updated_data = {
            "title": "And now for something completely different",
            "author": "Monty Python",
            "description": "Just Testing",
            "publication_date": "1970-01-01",
        }
        response = self.client.patch(self.book_detail_url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, updated_data["title"])
        self.assertEqual(self.book.author, updated_data["author"])
        self.assertEqual(self.book.description, updated_data["description"])
        self.assertEqual(
            self.book.publication_date, parse_date(updated_data["publication_date"])
        )

    def test_delete_book(self):
        response = self.client.delete(self.book_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)

    def test_duplicate_isbn(self):
        # Attempt to create a book with existing ISBN
        response = self.client.post(self.books_url, self.book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_isbn(self):
        invalid_book_data = self.book_data.copy()
        invalid_book_data["isbn"] = "123"  # Invalid ISBN
        response = self.client.post(self.books_url, invalid_book_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        cache.clear()


class FilteringTests(APITestCase):
    def setUp(self):
        self.book_data = {
            "isbn": "9780544003415",
            "title": "The Lord of the Rings",
            "author": "J.R.R. Tolkien",
            "description": "An epic fantasy novel",
            "publication_date": "1954-07-29",
        }
        self.book = Book.objects.create(**self.book_data)
        self.books_url = reverse("book-list")
        self.book_detail_url = reverse("book-detail", args=[self.book.isbn])

    def test_filter_books_by_author(self):
        response = self.client.get(f"{self.books_url}?author=Tolkien")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) == 1)

    def test_filter_books_by_publication_date(self):
        response = self.client.get(f"{self.books_url}?publication_date=1954-07-29")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) == 1)

    def filter_books_by_title(self):
        response = self.client.get(f"{self.books_url}?title=Lord")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) == 1)

    def tearDown(self):
        cache.clear()


class TestExternalData(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(
            isbn="1234567890",
            title="Test Book",
            author="Test Author",
            description="Test Description",
            publication_date="2023-01-01"
        )

    @patch("httpx.get")
    def test_retrieve_book_with_openlibrary_data(self, mock_get):
        # Setup mock response
        mock_get.return_value.json.return_value = {
            "title": "OpenLibrary Book",
            "authors": [{"name": "OpenLibrary Author"}]
        }

        # Make API request
        response = self.client.get(reverse("book-detail", args=[self.book.isbn]))

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn("raw_openlibrary_data", response.data)
        self.assertEqual(response.data["raw_openlibrary_data"]["title"], "OpenLibrary Book")
        mock_get.assert_called_once_with(
            f"https://openlibrary.org/isbn/{self.book.isbn}.json",
            follow_redirects=True,
            timeout=2
        )

    def tearDown(self):
        cache.clear()

class TestCache(APITestCase):
    def setUp(self):
        self.book_data = {
            "isbn": "1234567890",
            "title": "Test book",
            "author": "test author",
            "description": "empty description",
            "publication_date": "2023-01-01",
        }
        self.book = Book.objects.create(**self.book_data)
        self.books_url = reverse("book-list")
        self.book_detail_url = reverse("book-detail", args=[self.book.isbn])

    def test_cache_invalidates_on_book_update(self):
        # Mock first API call response
        first_response = {"key": "value1"}
        second_response = {"key": "value2"}

        with patch("httpx.get") as mock_request:
            # Setup mock responses
            mock_request.return_value.json.return_value = first_response
            response1 = self.client.get(self.book_detail_url)

            # Verify first response
            self.assertEqual(response1.data["raw_openlibrary_data"], first_response)

            # Second call should return cached first response
            response2 = self.client.get(self.book_detail_url)
            self.assertEqual(response2.data["raw_openlibrary_data"], first_response)

            # The library should be called only once
            mock_request.assert_called_once()

            # Update book to invalidate cache
            self.client.patch(self.book_detail_url, {"title": "Updated Title"})

            # Mock returns different response after cache invalidation
            # Also, mock call number is reset to 0
            mock_request.return_value.json.return_value = second_response
            mock_request.reset_mock()
            response3 = self.client.get(self.book_detail_url)

            # Verify we get the new response after cache invalidation
            self.assertEqual(response3.data["raw_openlibrary_data"], second_response)
            mock_request.assert_called_once()

    def tearDown(self):
        cache.clear()


class TestHttpxExceptions(APITestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.book_data = {
            "isbn": "1234567890",
            "title": "Test book",
            "author": "test author",
            "description": "empty description",
            "publication_date": "2023-01-01",
        }
        self.book = Book.objects.create(**self.book_data)
        self.books_url = reverse("book-list")
        self.book_detail_url = reverse("book-detail", args=[self.book.isbn])

    def test_connection_error(self):
        with patch("httpx.get") as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection failed")
            response = self.client.get(self.book_detail_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotIn("raw_openlibrary_data", response.data)
            self.assertEqual(response.data["isbn"], self.book.isbn)
            self.assertEqual(response.data["title"], self.book.title)
            self.assertEqual(response.data["author"], self.book.author)
            mock_request.assert_called_once()

    def test_timeout_error(self):
        with patch("httpx.get") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Request timed out")
            response = self.client.get(self.book_detail_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotIn("raw_openlibrary_data", response.data)
            self.assertEqual(response.data["isbn"], self.book.isbn)
            self.assertEqual(response.data["title"], self.book.title)
            self.assertEqual(response.data["author"], self.book.author)
            mock_request.assert_called_once()

    def test_http_error(self):
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPError("HTTP error ocurred")
            response = self.client.get(self.book_detail_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotIn("raw_openlibrary_data", response.data)
            self.assertEqual(response.data["isbn"], self.book.isbn)
            self.assertEqual(response.data["title"], self.book.title)
            self.assertEqual(response.data["author"], self.book.author)
            mock_get.assert_called_once()

    def test_json_decode_error(self):
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = JSONDecodeError("Invalid JSON", "", 0)
            response = self.client.get(self.book_detail_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotIn("raw_openlibrary_data", response.data)
            self.assertEqual(response.data["isbn"], self.book.isbn)
            self.assertEqual(response.data["title"], self.book.title)
            self.assertEqual(response.data["author"], self.book.author)
            mock_get.assert_called_once()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        cache.clear()
