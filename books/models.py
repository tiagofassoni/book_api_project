from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django_stubs_ext.db.models import TypedModelMeta


def somewhat_validate_isbn(isbn: str) -> None:
    """
    This is a very basic validation for ISBN.
    ISBNs do have validation in them (using the last digit), but there are literally published books with invalid ISBNs.
    So, instead of applying the full validation, we'll just check if the length is 10 or 13.
    If the length is 10, the last digit can either be a number or an X.
    """
    if len(isbn) not in (10, 13):
        raise ValidationError("ISBN must be 10 or 13 characters long")
    if len(isbn) == 10 and isbn[-1] not in "0123456789X":  #noqa: PLR2004
        raise ValidationError("ISBN must end with a number or an X if it's 10 characters long")
    if len(isbn) == 13 and not isbn.isdigit():  #noqa: PLR2004
        raise ValidationError("ISBN must be all digits if it's 13 characters long")

class Book(models.Model):


    author = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()
    isbn = models.TextField(max_length=13, primary_key=True, validators=[somewhat_validate_isbn])
    publication_date = models.DateField()
    title = models.TextField()

    class Meta(TypedModelMeta):
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["created_at"]),
        ]
        verbose_name: ClassVar[str] = "Book"
        verbose_name_plural: ClassVar[str] = "Books"
        ordering: ClassVar[list[str]] = ["created_at"]

    def __str__(self) -> str:
        return f"Book ISBN:{self.isbn} - {self.title}"
