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
            defaults={'monthly_budget': Decimal('1200.00'), 'currency_symbol': '$'}
        )

        today = timezone.localdate()
        curr_year = today.year
        curr_month = today.month

        # Clear existing expenses for a clean demo if specified
        sample_records = [
            (Expense.CATEGORY_HOUSING, Decimal('520.00'), 1, "Monthly Student Dorm / Housing Share"),
            (Expense.CATEGORY_GROCERIES, Decimal('54.30'), max(1, today.day - 9), "Weekly Groceries - Trader Joe's"),
            (Expense.CATEGORY_SUPPLIES, Decimal('82.50'), max(1, today.day - 8), "Organic Chemistry Textbook & Lab Manual"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('6.75'), max(1, today.day - 7), "Library Study Break Oat Latte"),
            (Expense.CATEGORY_TRANSPORT, Decimal('40.00'), max(1, today.day - 6), "Subsidized Campus Metro Pass"),
            (Expense.CATEGORY_GROCERIES, Decimal('26.40'), max(1, today.day - 5), "Farmers Market Fruit & Granola"),
            (Expense.CATEGORY_SUBSCRIPTIONS, Decimal('5.99'), max(1, today.day - 4), "Student Spotify & Streaming Bundle"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('16.50'), max(1, today.day - 3), "Campus Film Guild Ticket & Popcorn"),
            (Expense.CATEGORY_GROCERIES, Decimal('19.80'), max(1, today.day - 2), "Campus Dining Hall Meal Swipe"),
            (Expense.CATEGORY_SUPPLIES, Decimal('15.20'), max(1, today.day - 1), "Lecture Notes Binder & Highlighters"),
            (Expense.CATEGORY_OTHER, Decimal('10.00'), today.day, "Dorm Laundry Tokens & Quarters"),
            (Expense.CATEGORY_ENTERTAINMENT, Decimal('4.50'), today.day, "Cold Brew Coffee at Quad Kiosk"),
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

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} retro ledger records for {username}!"))
