from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import Expense, UserProfile
from decimal import Decimal
from datetime import date
from django.utils import timezone
import calendar


class Command(BaseCommand):
    help = "Seed realistic sample expenses for a user to demonstrate the retro tracker"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='student', help="Username to seed expenses for")

    def handle(self, *args, **options):
        username = options['username']
        user, created = User.objects.get_or_create(username=username, defaults={'email': f"{username}@university.edu"})
        if created:
            user.set_password('scholar123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}' (password: 'scholar123')"))

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'monthly_budget': Decimal('12000.00'), 'currency_symbol': '₹'}
        )

        today = timezone.localdate()
        curr_year = today.year
        curr_month = today.month

        sample_records = [
            (Expense.CATEGORY_HOUSING, Decimal('5500.00'), 1, "Monthly Student PG / Hostel Rent Share"),
            (Expense.CATEGORY_GROCERIES, Decimal('1850.00'), max(1, today.day - 9), "Monthly Mess & Grocery Provisions"),
            (Expense.CATEGORY_SUPPLIES, Decimal('750.00'), max(1, today.day - 8), "Engineering Textbooks & Lab Manual"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('180.00'), max(1, today.day - 7), "Campus Canteen Chai & Samosas"),
            (Expense.CATEGORY_TRANSPORT, Decimal('600.00'), max(1, today.day - 6), "Monthly Subsidized Metro & Bus Pass"),
            (Expense.CATEGORY_GROCERIES, Decimal('340.00'), max(1, today.day - 5), "Fresh Fruits & Nuts from Mandi"),
            (Expense.CATEGORY_SUBSCRIPTIONS, Decimal('119.00'), max(1, today.day - 4), "Student Spotify & YouTube Premium Pack"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('350.00'), max(1, today.day - 3), "Weekend Movie & Snacks with Friends"),
            (Expense.CATEGORY_GROCERIES, Decimal('120.00'), max(1, today.day - 2), "Campus Dining Hall Meal Coupons"),
            (Expense.CATEGORY_SUPPLIES, Decimal('80.00'), max(1, today.day - 1), "Graphite Pencils & Spiral Notebooks"),
            (Expense.CATEGORY_OTHER, Decimal('150.00'), today.day, "Hostel Laundry & Printing Tokens"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('60.00'), today.day, "Evening Cold Coffee at Campus Kiosk"),
        ]

        created_count = 0
        for cat, amt, d_num, note in sample_records:
            entry_date = date(curr_year, curr_month, max(1, min(d_num, calendar.monthrange(curr_year, curr_month)[1])))
            Expense.objects.create(
                user=user,
                category=cat,
                amount=amt,
                date=entry_date,
                notes=note
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} retro ledger records (INR) for {username}!"))


