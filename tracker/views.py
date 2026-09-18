import json
import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from .models import Expense, UserProfile
from .forms import UserRegistrationForm, UserLoginForm, ExpenseForm, BudgetUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create associated user profile with default student budget
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'monthly_budget': Decimal('1200.00'), 'currency_symbol': '$'}
            )
            
            login(request, user)
            messages.success(request, f"Welcome to the Ledger, Scholar {user.username}! Your student account is open.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}. Ledger retrieved.")
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials. Please verify your scholar ID and secret code.")
    else:
        form = UserLoginForm()

    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Ledger closed. You have been securely logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'monthly_budget': Decimal('1200.00'), 'currency_symbol': '$'}
    )

    today = timezone.localdate()

    # Determine selected month
    month_param = request.GET.get('month', '').strip()
    selected_year = today.year
    selected_month = today.month

    if month_param:
        try:
            parts = month_param.split('-')
            if len(parts) == 2:
                selected_year = int(parts[0])
                selected_month = int(parts[1])
                # validate bounds
                if not (1 <= selected_month <= 12 and 1900 <= selected_year <= 2100):
                    selected_year, selected_month = today.year, today.month
        except (ValueError, TypeError):
            selected_year, selected_month = today.year, today.month

    current_month_str = f"{selected_year:04d}-{selected_month:02d}"
    selected_month_date = date(selected_year, selected_month, 1)
    month_name = selected_month_date.strftime('%B %Y')
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    is_current_month = (selected_year == today.year and selected_month == today.month)

    # Base queryset for selected month
    month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=selected_year,
        date__month=selected_month
    )

    # Total spent in the month
    total_spent = month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_budget = profile.monthly_budget
    remaining_balance = monthly_budget - total_spent
    is_over_budget = remaining_balance < Decimal('0.00')

    # Budget percentage
    if monthly_budget > Decimal('0.00'):
        budget_pct = float((total_spent / monthly_budget) * Decimal('100.00'))
    else:
        budget_pct = 100.0 if total_spent > Decimal('0.00') else 0.0

    capped_budget_pct = min(100.0, budget_pct)

    # Status classification & theme color
    if budget_pct < 60.0:
        budget_status = "Safe"
        budget_theme_color = "#A3B899"  # Sage Green
        budget_badge_class = "bg-[#A3B899]/25 text-[#2e4028] border-[#A3B899]"
    elif budget_pct <= 85.0:
        budget_status = "Caution"
        budget_theme_color = "#E0A96D"  # Warm Ochre
        budget_badge_class = "bg-[#E0A96D]/25 text-[#54330d] border-[#E0A96D]"
    else:
        budget_status = "Warning" if not is_over_budget else "Exceeded"
        budget_theme_color = "#D98880"  # Dusty Rose / Coral
        budget_badge_class = "bg-[#D98880]/25 text-[#58211c] border-[#D98880]"

    # Daily safe-to-spend allowance
    if is_current_month:
        # Days remaining including today
        days_remaining = max(1, (days_in_month - today.day) + 1)
        if remaining_balance > Decimal('0.00'):
            daily_safe_spend = (remaining_balance / Decimal(days_remaining)).quantize(Decimal('0.01'))
        else:
            daily_safe_spend = Decimal('0.00')
        days_remaining_text = f"{days_remaining} day{'s' if days_remaining != 1 else ''} remaining in {today.strftime('%B')}"
    elif selected_month_date < date(today.year, today.month, 1):
        days_remaining = 0
        daily_safe_spend = Decimal('0.00')
        days_remaining_text = "Concluded ledger month"
    else:
        days_remaining = days_in_month
        if remaining_balance > Decimal('0.00'):
            daily_safe_spend = (remaining_balance / Decimal(days_remaining)).quantize(Decimal('0.01'))
        else:
            daily_safe_spend = Decimal('0.00')
        days_remaining_text = f"{days_in_month} days in upcoming month"

    # Charts Data Preparation
    # 1. Category Breakdown Doughnut Chart
    cat_aggregates = (
        month_expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    chart_category_labels = []
    chart_category_data = []
    chart_category_colors = []
    chart_category_borders = []

    for item in cat_aggregates:
        cat_key = item['category']
        meta = Expense.CATEGORY_METADATA.get(cat_key, Expense.CATEGORY_METADATA[Expense.CATEGORY_OTHER])
        label = f"{meta['icon']} {meta['name']}"
        chart_category_labels.append(label)
        chart_category_data.append(float(item['total']))
        chart_category_colors.append(meta['bg'])
        chart_category_borders.append('#3E2723')

    # 2. Monthly Trend Line Chart (Day 1 to days_in_month)
    daily_spend_dict = {day: 0.0 for day in range(1, days_in_month + 1)}
    for exp in month_expenses:
        if exp.date.year == selected_year and exp.date.month == selected_month:
            daily_spend_dict[exp.date.day] = daily_spend_dict.get(exp.date.day, 0.0) + float(exp.amount)

    chart_trend_labels = [f"{d}" for d in range(1, days_in_month + 1)]
    chart_trend_daily_data = [round(daily_spend_dict[d], 2) for d in range(1, days_in_month + 1)]

    # Cumulative trend data
    running_sum = 0.0
    chart_trend_cumulative_data = []
    for d in range(1, days_in_month + 1):
        running_sum += daily_spend_dict[d]
        chart_trend_cumulative_data.append(round(running_sum, 2))

    # Filters for ledger list
    category_filter = request.GET.get('category', '').strip()
    search_query = request.GET.get('search', '').strip()

    filtered_expenses = month_expenses
    if category_filter and category_filter in dict(Expense.CATEGORY_CHOICES):
        filtered_expenses = filtered_expenses.filter(category=category_filter)

    if search_query:
        filtered_expenses = filtered_expenses.filter(
            Q(notes__icontains=search_query) |
            Q(amount__icontains=search_query)
        )

    filtered_total = filtered_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Month options for selector (last 6 months and next month)
    month_options = []
    base_calc_date = date(today.year, today.month, 1)
    for offset in range(-5, 2):
        # Calculate target month
        calc_m = (base_calc_date.month - 1 + offset) % 12 + 1
        calc_y = base_calc_date.year + ((base_calc_date.month - 1 + offset) // 12)
        opt_val = f"{calc_y:04d}-{calc_m:02d}"
        opt_label = date(calc_y, calc_m, 1).strftime('%B %Y')
        month_options.append({
            'value': opt_val,
            'label': opt_label,
            'selected': opt_val == current_month_str
        })

    # Initialize forms
    expense_form = ExpenseForm(initial={
        'date': today.strftime('%Y-%m-%d'),
        'category': Expense.CATEGORY_GROCERIES
    })
    budget_form = BudgetUpdateForm(instance=profile)

    context = {
        'profile': profile,
        'today': today,
        'selected_month_str': current_month_str,
        'month_name': month_name,
        'days_in_month': days_in_month,
        'is_current_month': is_current_month,
        'total_spent': total_spent,
        'monthly_budget': monthly_budget,
        'remaining_balance': remaining_balance,
        'is_over_budget': is_over_budget,
        'budget_pct': round(budget_pct, 1),
        'capped_budget_pct': round(capped_budget_pct, 1),
        'budget_status': budget_status,
        'budget_theme_color': budget_theme_color,
        'budget_badge_class': budget_badge_class,
        'daily_safe_spend': daily_safe_spend,
        'days_remaining': days_remaining,
        'days_remaining_text': days_remaining_text,
        'expenses': filtered_expenses,
        'total_count': filtered_expenses.count(),
        'filtered_total': filtered_total,
        'all_categories': Expense.CATEGORY_CHOICES,
        'selected_category': category_filter,
        'search_query': search_query,
        'month_options': month_options,
        'expense_form': expense_form,
        'budget_form': budget_form,
        # Serialized JSON for Chart.js
        'chart_category_labels_json': json.dumps(chart_category_labels),
        'chart_category_data_json': json.dumps(chart_category_data),
        'chart_category_colors_json': json.dumps(chart_category_colors),
        'chart_category_borders_json': json.dumps(chart_category_borders),
        'chart_trend_labels_json': json.dumps(chart_trend_labels),
        'chart_trend_daily_data_json': json.dumps(chart_trend_daily_data),
        'chart_trend_cumulative_data_json': json.dumps(chart_trend_cumulative_data),
        'has_expenses': month_expenses.exists(),
    }

    return render(request, 'tracker/dashboard.html', context)


@login_required
@require_POST
def add_expense_view(request):
    form = ExpenseForm(request.POST)
    month = request.POST.get('month', '')
    if form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.save()
        messages.success(
            request, 
            f"Voucher recorded: {expense.get_category_display()} for ${expense.amount:.2f}."
        )
        # Redirect back to the expense's month so user sees it right away
        target_month = expense.date.strftime('%Y-%m')
        return redirect(f"/dashboard/?month={target_month}")
    else:
        messages.error(request, "Failed to record expense. Please correct the highlighted entries.")
        redirect_url = f"/dashboard/?month={month}" if month else "/dashboard/"
        return redirect(redirect_url)


@login_required
def edit_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            saved_expense = form.save()
            messages.success(
                request, 
                f"Ledger voucher #{saved_expense.id} successfully amended."
            )
            target_month = saved_expense.date.strftime('%Y-%m')
            return redirect(f"/dashboard/?month={target_month}")
        else:
            messages.error(request, "Please check your ledger amendments.")
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'tracker/edit_expense.html', {
        'form': form,
        'expense': expense
    })


@login_required
@require_POST
def delete_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    target_month = expense.date.strftime('%Y-%m')
    amount = expense.amount
    category = expense.get_category_display()
    expense.delete()
    messages.success(request, f"Voided voucher: {category} (${amount:.2f}) removed from ledger.")
    return redirect(f"/dashboard/?month={target_month}")


@login_required
@require_POST
def update_budget_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = BudgetUpdateForm(request.POST, instance=profile)
    month = request.POST.get('month', '')
    if form.is_valid():
        form.save()
        messages.success(request, f"Monthly budget limit updated to ${profile.monthly_budget:.2f}.")
    else:
        messages.error(request, "Invalid budget amount. Please specify a positive figure.")
    
    redirect_url = f"/dashboard/?month={month}" if month else "/dashboard/"
    return redirect(redirect_url)


@login_required
def seed_demo_data_view(request):
    """Seed realistic student expenses for instant demonstration."""
    today = timezone.localdate()
    curr_year = today.year
    curr_month = today.month

    # Generate diverse student entries
    sample_records = [
        (Expense.CATEGORY_HOUSING, Decimal('520.00'), min(1, today.day), "Monthly Student Dorm / Housing Share"),
        (Expense.CATEGORY_GROCERIES, Decimal('48.60'), max(1, today.day - 7), "Weekly Groceries - Trader Joe's"),
        (Expense.CATEGORY_SUPPLIES, Decimal('72.50'), max(1, today.day - 6), "Organic Chemistry Textbook & Notebooks"),
        (Expense.CATEGORY_ENTERTAINMENT, Decimal('6.85'), max(1, today.day - 5), "Study Break Iced Oat Latte"),
        (Expense.CATEGORY_TRANSPORT, Decimal('35.00'), max(1, today.day - 4), "Subsidized Campus Metro Pass"),
        (Expense.CATEGORY_GROCERIES, Decimal('21.40'), max(1, today.day - 3), "Farmers Market Produce & Oats"),
        (Expense.CATEGORY_SUBSCRIPTIONS, Decimal('5.99'), max(1, today.day - 3), "Student Spotify & Streaming Pack"),
        (Expense.CATEGORY_ENTERTAINMENT, Decimal('14.20'), max(1, today.day - 2), "Campus Film Club Screening & Snacks"),
        (Expense.CATEGORY_GROCERIES, Decimal('16.80'), max(1, today.day - 1), "Campus Dining Hall Lunch Voucher"),
        (Expense.CATEGORY_SUPPLIES, Decimal('12.75'), today.day, "Graphite Pencils & Index Cards"),
        (Expense.CATEGORY_OTHER, Decimal('9.50'), today.day, "Dorm Laundry Tokens"),
    ]

    count_created = 0
    for cat, amt, d_num, note in sample_records:
        entry_date = date(curr_year, curr_month, max(1, min(d_num, calendar.monthrange(curr_year, curr_month)[1])))
        Expense.objects.create(
            user=request.user,
            category=cat,
            amount=amt,
            date=entry_date,
            notes=note
        )
        count_created += 1

    messages.success(
        request, 
        f"Archived {count_created} sample student expense vouchers into your ledger!"
    )
    return redirect(f"/dashboard/?month={curr_year:04d}-{curr_month:02d}")
