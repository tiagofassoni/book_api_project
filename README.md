# Books API

A simple API for managing books. The API allows standard CRUD operations and filtering. 
Books are stored by unique ISBNs and can be retrieved by ISBN or by lookup from its other fields, like date and author.

The book detail endpoint provides extra data from openlibrary API, which is not stored in the database but cached on demand.
Errors on the openlibrary API will return just the internal data and log an error internally.

Updating a book will invalidate the cache for that same book. Retrieving a book will cache it for 5 minutes by default.

List requests are not cached, but are paginated.

Please note this API is intended for internal consumption only, as there is absolutely no authentication or authorization implemented.

A browsable UI is available at the endpoint `/swagger-ui/`.


## Architectural Decisions

The API assumes ISBNs are unique for ease of implementation. That is not completely true, there are some ISBNs that are 
shared among several works, mostly for older works. Also, ISBN does have built-in checksums, but there are actual published
works with invalid ISBNs, so the API provides only very basic validation. The validation code is in books/models.py.

This project tries to stay very close to Django and big Django-based projects.
Doing so ensures things are well-tested and we also get  a lot of tooling and extra functionality out of the box. 
For example, Django Rest Framework's ModelViewSet provides filtering out of the box and pagination is trivial to add and 
drf-spectacular provides a nice UI for the API with documentation with very little effort.

This project does _not_ use Django's async functionality for some reasons:
- caching in Django 5.1 is not async
- Django Rest Framework does not support async out of the box (and the most expensive call uses caching, which isn't async)
- This API is not built for performance at scale, it is built for simplicity and ease of development.

For external data, we use OpenLibrary's API as it is very simple to integrate and it is free to use.
Httpx is used for the API calls instead of the more popular requests library because httpx can be easily turned async.

Caching for the Book detail view uses Redis and Django's cache backend. 
The functionality is provided as a decorator, the rather lengthy `viewset_cache_detail_with_reset_on_update` in decorators.py

### Technical Debt
- Typing information is missing in many places
- Requirements need to be properly separated in dev/prod, with appropriate containers.
- Proper permissions must be added.


## Development
The development environment is built with Docker Compose. The compose environment needs a .env file. 
Please copy the .env.example file and fill in the values.

To initialize the environment, run:
```
docker-compose up 
```
And inside another container run the migrations:
```bash
docker compose run web bash
python manage.py migrate
```

Seed data is available in the sample_books.json file. We also provide a simple script to populate the database with the data.
Please note the script must run outside the container.
```bash
python populate_database_via_cli.py
```

### Tests, Linting, Coverage and Type Checking

The following commands are availabe inside the `web` container. 
To run them, you must first run `docker compose run web bash`

Tests use standard django tooling:
```bash
python manage.py test
```

Code coverage needs the first command for discovery, the second to show you a report:
```bash
coverage run manage.py test
coverage report
```

For linting, we use ruff:
```bash
ruff check .
```

Type checking is available with mypy:
```bash
mypy .
```

