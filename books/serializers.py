from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from books.models import Book


class BookSerializer(ModelSerializer[Book]):

    class Meta:
        model = Book
        fields = "__all__"

    def update(self, instance, validated_data):
        if "isbn" in validated_data and instance.isbn != validated_data["isbn"]:
            raise ValidationError(
                {"isbn": "This field cannot be updated. If you need to update it, delete the book and create a new one."}
            )
        return super().update(instance, validated_data)
