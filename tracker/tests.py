from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date
from django.utils import timezone
import calendar

from .models import Expense, UserProfile


class ExpenseTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create primary test user
        self.user1 = User.objects.create_user(
            username='scholar_alice',
            email='alice@university.edu',
            password='password123'
        )
        self.profile1 = UserProfile.objects.create(
            user=self.user1,
            monthly_budget=Decimal('1000.00')
        )

        # Create secondary test user for isolation tests
        self.user2 = User.objects.create_user(
            username='scholar_bob',
            email='bob@university.edu',
            password='password456'
        )
        self.profile2 = UserProfile.objects.create(
            user=self.user2,
            monthly_budget=Decimal('800.00')
        )

        self.today = timezone.localdate()

    def test_model_creation_and_properties(self):
        exp = Expense.objects.create(
            user=self.user1,
            category=Expense.CATEGORY_GROCERIES,
            amount=Decimal('45.50'),
            date=self.today,
            notes="Farmer market apples"
        )
        self.assertEqual(exp.user, self.user1)
        self.assertEqual(exp.amount, Decimal('45.50'))
        self.assertEqual(exp.icon, '🍎')
        self.assertIn('bg', exp.metadata)
        self.assertIn('$45.50', str(exp))

    def test_protected_routes_redirect_unauthenticated(self):
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_user_registration(self):
        register_url = reverse('register')
        response = self.client.post(register_url, {
            'username': 'new_scholar',
            'email': 'new@university.edu',
            'password': 'safePassword99',
            'confirm_password': 'safePassword99'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='new_scholar').exists())
        new_user = User.objects.get(username='new_scholar')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.monthly_budget, Decimal('1200.00'))

    def test_dashboard_calculations_and_daily_safe_spend(self):
        self.client.login(username='scholar_alice', password='password123')
        
        # Log 2 expenses for current month
        Expense.objects.create(
            user=self.user1,
            category=Expense.CATEGORY_HOUSING,
            amount=Decimal('400.00'),
            date=self.today,
            notes="Rent payment"
        )
        Expense.objects.create(
            user=self.user1,
            category=Expense.CATEGORY_GROCERIES,
            amount=Decimal('100.00'),
            date=self.today,
            notes="Weekly grocery"
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_spent'], Decimal('500.00'))
        self.assertEqual(response.context['remaining_balance'], Decimal('500.00'))
        self.assertEqual(response.context['budget_pct'], 50.0)
        self.assertEqual(response.context['budget_status'], 'Safe')

        # Verify daily safe-to-spend calculation
        days_in_month = calendar.monthrange(self.today.year, self.today.month)[1]
        days_remaining = (days_in_month - self.today.day) + 1
        expected_daily_spend = (Decimal('500.00') / Decimal(days_remaining)).quantize(Decimal('0.01'))
        self.assertEqual(response.context['daily_safe_spend'], expected_daily_spend)

    def test_crud_expense_workflow(self):
        self.client.login(username='scholar_alice', password='password123')

        # 1. CREATE
        add_url = reverse('add_expense')
        response = self.client.post(add_url, {
            'amount': '35.00',
            'category': Expense.CATEGORY_SUPPLIES,
            'date': self.today.strftime('%Y-%m-%d'),
            'notes': 'Physics Lab Manual'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.filter(user=self.user1).count(), 1)
        expense = Expense.objects.filter(user=self.user1).first()
        self.assertEqual(expense.amount, Decimal('35.00'))

        # 2. READ / EDIT
        edit_url = reverse('edit_expense', kwargs={'pk': expense.pk})
        get_edit = self.client.get(edit_url)
        self.assertEqual(get_edit.status_code, 200)

        # 3. UPDATE
        post_edit = self.client.post(edit_url, {
            'amount': '42.50',
            'category': Expense.CATEGORY_SUPPLIES,
            'date': self.today.strftime('%Y-%m-%d'),
            'notes': 'Physics Lab Manual & Ruler'
        })
        self.assertEqual(post_edit.status_code, 302)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal('42.50'))
        self.assertEqual(expense.notes, 'Physics Lab Manual & Ruler')

        # 4. DELETE
        delete_url = reverse('delete_expense', kwargs={'pk': expense.pk})
        del_response = self.client.post(delete_url)
        self.assertEqual(del_response.status_code, 302)
        self.assertEqual(Expense.objects.filter(user=self.user1).count(), 0)

    def test_per_user_data_isolation(self):
        # Create an expense for user 2 (Bob)
        bobs_expense = Expense.objects.create(
            user=self.user2,
            category=Expense.CATEGORY_TRANSPORT,
            amount=Decimal('50.00'),
            date=self.today,
            notes="Bob transit pass"
        )

        # Alice logs in
        self.client.login(username='scholar_alice', password='password123')

        # Alice cannot see Bob's expense on dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertNotIn(b"Bob transit pass", response.content)
        self.assertEqual(response.context['expenses'].count(), 0)

        # Alice cannot edit Bob's expense (should return 404)
        edit_url = reverse('edit_expense', kwargs={'pk': bobs_expense.pk})
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404)

        # Alice cannot delete Bob's expense (should return 404)
        del_url = reverse('delete_expense', kwargs={'pk': bobs_expense.pk})
        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=bobs_expense.pk).exists())

    def test_budget_update(self):
        self.client.login(username='scholar_alice', password='password123')
        update_budget_url = reverse('update_budget')
        response = self.client.post(update_budget_url, {
            'monthly_budget': '1500.00'
        })
        self.assertEqual(response.status_code, 302)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.monthly_budget, Decimal('1500.00'))
