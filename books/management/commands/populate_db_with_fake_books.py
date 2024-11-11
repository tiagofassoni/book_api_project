# ruff: noqa: T201
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from faker import Faker
from tqdm import tqdm

from books.models import Book


class Command(BaseCommand):
    help = "Populates the database with sample data. Please note the books generated are not valid ISBNs and won't work with OpenLibrary API. They are only for testing purposes."

    def add_arguments(self, parser):
        parser.add_argument("--amount", type=int, help="The number of fake books that should be created.")
        parser.add_argument("--bulk_count", type=int, help="How many books to insert in a single bulk insert. Must be a divider of amount.")
        parser.add_argument("--seed", type=int, help="Seed for Faker instance")

    def handle(self, *args, **options):
        amount = options["amount"] if options["amount"] else 2_000_000
        bulk_count = options["bulk_count"] if options["bulk_count"] else 10_000
        seed = options["seed"] if options["seed"] else 12345

        if amount % bulk_count != 0:
            raise ValueError("bulk_count must be a divider of amount")

        Faker.seed(seed)
        fake = Faker()

        if Book.objects.count() > 0:
            print("Database already contains data. Exiting...")
            return

        # Create `amount` of books
        print("Moving onto creation of purchases. This may take a while...")
        bulk_count = 10_000
        for _ in tqdm(range(0, amount, bulk_count)):
            books = [
                Book(
                    author=fake.name(),
                    description=fake.text(),
                    isbn=fake.unique.isbn13(separator=""),
                    title=fake.sentence(nb_words=5, variable_nb_words=True),
                    publication_date=parse_date(fake.date()),
                )
                for _ in range(bulk_count)
            ]
            Book.objects.bulk_create(books)

        print("Successfully populated the database.")
