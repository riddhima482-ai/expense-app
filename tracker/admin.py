from django.contrib import admin
from .models import UserProfile, Expense


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_budget', 'currency_symbol')
    search_fields = ('user__username', 'user__email')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'category', 'amount', 'notes', 'created_at')
    list_filter = ('category', 'date', 'user')
    search_fields = ('notes', 'user__username')
    date_hierarchy = 'date'
