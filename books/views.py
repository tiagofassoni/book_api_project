import logging
import textwrap
from json import JSONDecodeError

import httpx
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from books.decorators import viewset_cache_detail_with_reset_on_update
from books.models import Book
from books.paginators import BookPagination
from books.serializers import BookSerializer

logger = logging.getLogger(__name__)


@viewset_cache_detail_with_reset_on_update(timeout=60 * 5)
@extend_schema_view(
    create=extend_schema(description="Inserts a new book, using ISBN as primary key"),
    destroy=extend_schema(description="Deletes the book with given ISBN"),
    list=extend_schema(
        description="Retrieves all the books in the system with pagination. Default is 10 items per page, ordered by creation date."
    ),
    partial_update=extend_schema(
        description=textwrap.dedent(
            """
            Updates the book with given ISBN. Only the fields provided in the request body will be updated.
            ISBN is immutable and cannot be updated. If you need to change the ISBN, delete the book and create a new one.
            """
        )
    ),
    retrieve=extend_schema(
        description=textwrap.dedent(
            """
            Retrieves a book by ISBN.
            We also try to get extra data from openlibrary API and make it available in the field `raw_openlibrary_data`.
            OpenLibrary API data is cached for 5 minutes by default, but the cache can be invalidated by updating the book.
        
            If, for some reason, the openlibrary API fails, we return the internal data only and log the failure.
            """
        ),
        responses={
            200: inline_serializer(
                name="BookWithOpenLibrary",
                fields={
                    **BookSerializer().fields,
                    "raw_openlibrary_data": serializers.JSONField(required=False),
                },
            )
        },
    ),
    update=extend_schema(description="Updates the book with given ISBN. You need to send an entire book object, minus ISBN"),
)
class BookViewSet(ModelViewSet[Book]):

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = BookPagination
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Try to get extra data from openlibrary API, or none if it fails
        try:
            #  OpenLibrary API by default moves us to its own identifier, so we need to follow the redirect
            response = httpx.get(
                f"https://openlibrary.org/isbn/{instance.isbn}.json",
                follow_redirects=True,
                timeout=2,
            )
            if response.json():
                return Response(
                    {**serializer.data, "raw_openlibrary_data": response.json()}
                )
        except httpx.ConnectError:
            logger.exception(
                "Connection error in OpenLibrary API on ISBN %(isbn):",
                extra={"isbn": instance.isbn},
            )
        except httpx.TimeoutException:
            logger.exception(
                "Timeout in OpenLibrary API on ISBN  %(isbn):",
                extra={"isbn": instance.isbn},
            )
        except httpx.HTTPError:
            logger.exception(
                "HTTP error in OpenLibrary on ISBN %(isbn):",
                extra={"isbn": instance.isbn},
            )
        except JSONDecodeError:
            logger.exception(
                "Invalid JSON received from OpenLibrary on ISBN %(isbn):",
                extra={"isbn": instance.isbn},
            )

        return Response(serializer.data)
