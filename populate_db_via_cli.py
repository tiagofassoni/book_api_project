# ruff: noqa

import httpx
import json

with open('sample_books.json') as json_file:
    books = json.load(json_file)

for book in books:
    url = 'http://localhost:8000/books/'
    response = httpx.post(url, json=book)
    print(f"{response.status_code} - {response.text}")