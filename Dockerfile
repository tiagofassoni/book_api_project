FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the project into the image
ADD . .

CMD ["gunicorn", "book_api_project.wsgi", "--bind", "0.0.0.0:8000"]