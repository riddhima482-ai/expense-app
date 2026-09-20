from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    monthly_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('12000.00'),
        help_text="Target budget for each calendar month."
    )
    currency_symbol = models.CharField(max_length=5, default='₹')

    def __str__(self):
        return f"{self.user.username}'s Ledger Profile (₹{self.monthly_budget})"



class Expense(models.Model):
    CATEGORY_GROCERIES = 'groceries'
    CATEGORY_HOUSING = 'housing'
    CATEGORY_SUPPLIES = 'supplies'
    CATEGORY_TRANSPORT = 'transport'
    CATEGORY_ENTERTAINMENT = 'entertainment'
    CATEGORY_SUBSCRIPTIONS = 'subscriptions'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_GROCERIES, 'Groceries & Food'),
        (CATEGORY_HOUSING, 'Campus Housing / Rent'),
        (CATEGORY_SUPPLIES, 'Books & Supplies'),
        (CATEGORY_TRANSPORT, 'Transport & Transit'),
        (CATEGORY_ENTERTAINMENT, 'Coffee & Leisure'),
        (CATEGORY_SUBSCRIPTIONS, 'Tech & Subscriptions'),
        (CATEGORY_OTHER, 'Miscellaneous'),
    ]

    CATEGORY_METADATA = {
        CATEGORY_GROCERIES: {
            'name': 'Groceries & Food',
            'icon': '🍎',
            'bg': '#A3B899',       # Sage Green
            'text': '#1D2A1C',
            'badge_bg': 'bg-[#A3B899]/25',
            'badge_border': 'border-[#A3B899]',
            'badge_text': 'text-[#2e4028]',
        },
        CATEGORY_HOUSING: {
            'name': 'Campus Housing / Rent',
            'icon': '🏠',
            'bg': '#D98880',       # Dusty Rose
            'text': '#3D1C1A',
            'badge_bg': 'bg-[#D98880]/25',
            'badge_border': 'border-[#D98880]',
            'badge_text': 'text-[#58211c]',
        },
        CATEGORY_SUPPLIES: {
            'name': 'Books & Supplies',
            'icon': '📚',
            'bg': '#B39DDB',       # Muted Lavender
            'text': '#2A1B40',
            'badge_bg': 'bg-[#B39DDB]/25',
            'badge_border': 'border-[#B39DDB]',
            'badge_text': 'text-[#3c255e]',
        },
        CATEGORY_TRANSPORT: {
            'name': 'Transport & Transit',
            'icon': '🚌',
            'bg': '#E0A96D',       # Warm Ochre
            'text': '#38220B',
            'badge_bg': 'bg-[#E0A96D]/25',
            'badge_border': 'border-[#E0A96D]',
            'badge_text': 'text-[#54330d]',
        },
        CATEGORY_ENTERTAINMENT: {
            'name': 'Coffee & Leisure',
            'icon': '☕',
            'bg': '#E27D60',       # Soft Coral
            'text': '#381A12',
            'badge_bg': 'bg-[#E27D60]/25',
            'badge_border': 'border-[#E27D60]',
            'badge_text': 'text-[#5c2415]',
        },
        CATEGORY_SUBSCRIPTIONS: {
            'name': 'Tech & Subscriptions',
            'icon': '📱',
            'bg': '#82A6A2',       # Vintage Teal
            'text': '#152927',
            'badge_bg': 'bg-[#82A6A2]/25',
            'badge_border': 'border-[#82A6A2]',
            'badge_text': 'text-[#1c3e3a]',
        },
        CATEGORY_OTHER: {
            'name': 'Miscellaneous',
            'icon': '🏷️',
            'bg': '#D6CEBE',       # Antique Buff
            'text': '#2E2B25',
            'badge_bg': 'bg-[#D6CEBE]/35',
            'badge_border': 'border-[#D6CEBE]',
            'badge_text': 'text-[#3E2723]',
        },
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_GROCERIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, help_text="Payee, item, or memo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.get_category_display()} - ₹{self.amount}"


    @property
    def metadata(self):
        return self.CATEGORY_METADATA.get(self.category, self.CATEGORY_METADATA[self.CATEGORY_OTHER])

    @property
    def icon(self):
        return self.metadata['icon']
