from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Expense, UserProfile
from decimal import Decimal


VINTAGE_INPUT_CLASSES = (
    "w-full bg-[#FDFBF7] text-[#2C2C2C] border-2 border-[#3E2723] rounded-lg "
    "px-3.5 py-2.5 text-sm font-sans focus:outline-none focus:ring-2 "
    "focus:ring-[#A3B899] shadow-[2px_2px_0px_#3E2723] transition-all"
)

VINTAGE_SELECT_CLASSES = (
    "w-full bg-[#FDFBF7] text-[#2C2C2C] border-2 border-[#3E2723] rounded-lg "
    "px-3.5 py-2.5 text-sm font-sans focus:outline-none focus:ring-2 "
    "focus:ring-[#A3B899] shadow-[2px_2px_0px_#3E2723] transition-all cursor-pointer"
)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': VINTAGE_INPUT_CLASSES,
            'placeholder': 'Choose a secure secret code',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': VINTAGE_INPUT_CLASSES,
            'placeholder': 'Re-enter your secret code',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': VINTAGE_INPUT_CLASSES,
                'placeholder': 'e.g. riddhima_scholar',
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'class': VINTAGE_INPUT_CLASSES,
                'placeholder': 'student@university.edu',
                'autocomplete': 'email'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This scholar username is already enrolled in the ledger.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Secret passwords do not match. Please verify.")
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': VINTAGE_INPUT_CLASSES,
            'placeholder': 'Scholar ID / Username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': VINTAGE_INPUT_CLASSES,
            'placeholder': 'Secret code',
            'autocomplete': 'current-password'
        })
    )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': VINTAGE_INPUT_CLASSES + " font-mono text-base font-semibold",
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'category': forms.Select(attrs={
                'class': VINTAGE_SELECT_CLASSES
            }),
            'date': forms.DateInput(attrs={
                'class': VINTAGE_INPUT_CLASSES + " font-mono",
                'type': 'date'
            }),
            'notes': forms.TextInput(attrs={
                'class': VINTAGE_INPUT_CLASSES,
                'placeholder': 'e.g., Campus Bookstore, Trader Joe\'s, Bus Pass...'
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= Decimal('0.00'):
            raise forms.ValidationError("Expense amount must be greater than zero.")
        return amount


class BudgetUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['monthly_budget']
        labels = {
            'monthly_budget': 'Monthly Budget Target (₹)'
        }
        widgets = {
            'monthly_budget': forms.NumberInput(attrs={
                'class': VINTAGE_INPUT_CLASSES + " font-mono text-base font-semibold",
                'step': '100.00',
                'min': '100.00',
                'placeholder': '12000.00'
            }),
        }

