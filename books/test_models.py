from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from books.models import Book, somewhat_validate_isbn


class ISBNValidatorTests(TestCase):
    def test_valid_isbn_10(self):
        valid_isbn_10 = "0747532699"
        somewhat_validate_isbn(valid_isbn_10)  # Should not raise

    def test_valid_isbn_10_with_x(self):
        valid_isbn_10_x = "155404295X"
        somewhat_validate_isbn(valid_isbn_10_x)  # Should not raise

    def test_valid_isbn_13(self):
        valid_isbn_13 = "9780747532743"
        somewhat_validate_isbn(valid_isbn_13)  # Should not raise

    def test_invalid_isbn_length(self):
        invalid_isbn = "12345"
        with self.assertRaises(ValidationError):
            somewhat_validate_isbn(invalid_isbn)

    def test_invalid_isbn_10_with_letter(self):
        invalid_isbn = "074753269A"
        with self.assertRaises(ValidationError):
            somewhat_validate_isbn(invalid_isbn)

    def test_invalid_isbn_13_with_letter(self):
        invalid_isbn = "978074753274X"
        with self.assertRaises(ValidationError):
            somewhat_validate_isbn(invalid_isbn)


class BookModelTests(TestCase):
    def setUp(self):
        self.book_data = {
            "isbn": "9780747532743",
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description",
            "publication_date": date(2023, 1, 1),
        }

    def test_create_book(self):
        book = Book.objects.create(**self.book_data)
        self.assertEqual(book.isbn, self.book_data["isbn"])
        self.assertEqual(book.title, self.book_data["title"])
        self.assertEqual(book.author, self.book_data["author"])
        self.assertEqual(book.description, self.book_data["description"])
        self.assertEqual(book.publication_date, self.book_data["publication_date"])

    def test_book_str_representation(self):
        book = Book.objects.create(**self.book_data)
        expected_str = f"Book ISBN:{self.book_data['isbn']} - {self.book_data['title']}"
        self.assertEqual(str(book), expected_str)

    def test_book_ordering(self):
        # Book created first should be first in the ordered set
        book1 = Book.objects.create(**self.book_data)

        book2_data = self.book_data.copy()
        book2_data["isbn"] = "9780747532744"
        book2 = Book.objects.create(**book2_data)

        # Get ordered books
        books = Book.objects.all()
        self.assertEqual(books[0], book1)
        self.assertEqual(books[1], book2)

    def test_invalid_isbn_validation(self):
        invalid_book_data = self.book_data.copy()
        invalid_book_data["isbn"] = "123"  # Invalid ISBN

        with self.assertRaises(ValidationError):
            book = Book(**invalid_book_data)
            book.full_clean()
