import random
from django.core.management.base import BaseCommand
from listings.models import Listing, User
from decimal import Decimal
import uuid

class Command(BaseCommand):
    help = 'Seed the database with sample listings data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        self.stdout.write("Deleting existing listings...")
        Listing.objects.all().delete()

        # Create sample users (hosts)
        self.stdout.write("Creating sample users...")
        users = [
            User.objects.create_user(
                username=f'host{i}',
                email=f'host{i}@example.com',
                password='password123'
            )
            for i in range(1, 6)  # Create 5 users
        ]

        # Create sample listings
        self.stdout.write("Creating sample listings...")
        locations = ['New York', 'Paris', 'Tokyo', 'London', 'Berlin']
        amenities = ['Wi-Fi', 'TV', 'Air Conditioning', 'Heating', 'Kitchen']

        for i in range(10):  # Create 10 sample listings
            host = random.choice(users)
            listing = Listing.objects.create(
                property_id=uuid.uuid4(),
                host=host,
                name=f'Sample Listing {i+1}',
                description=f'This is a description for Sample Listing {i+1}.',
                location=random.choice(locations),
                price_per_night=Decimal(random.randint(50, 300)),
            )
            self.stdout.write(self.style.SUCCESS(f'Created listing: {listing.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!'))
