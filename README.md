# 📜 Scholar Ledger — Vintage Pastel Student Expense Tracker

A full-stack student expense tracker built with **Django 5** and styled using **Tailwind CSS** with a retro vintage aesthetic, soft pastel color palette, tactile neo-brutalist card shadows, and old-school accounting ledger paper styling.

---

## 🎨 Aesthetic & UI/UX Design System

- **Backgrounds**: Warm Parchment (`#FDFBF7`), Vintage Card Paper (`#F7F4EA`), Card Inset (`#EFE9DC`).
- **Typography**: 
  - Serif Display: *Playfair Display* & *Lora* for ledger headers and classical seals.
  - Typewriter / Monospace: *Courier Prime* for amounts, transaction dates, and stamps.
  - Body Sans: *Plus Jakarta Sans* for clean, legible form inputs and data labels.
- **Pastel Accent Palette**:
  - **Dusty Rose** (`#D98880`): Housing / Rent & critical deficit alerts
  - **Sage Green** (`#A3B899`): Groceries & healthy budget indicator
  - **Muted Lavender** (`#B39DDB`): Books, supplies & daily pacing
  - **Warm Ochre** (`#E0A96D`): Transport & cautionary budget indicator
  - **Soft Coral** (`#E27D60`): Coffee & entertainment
  - **Vintage Teal** (`#82A6A2`): Tech & recurring subscriptions
- **Retro Details**: Neo-brutalist solid drop shadows (`box-shadow: 4px 4px 0px #3E2723`), double-underline accounting footers, dashed library card borders, and ink-stamped badges.

---

## ⚡ Key Features

1. **Authentication System (Django Auth)**:
   - Retro library borrower card styled login and registration views.
   - Strictly isolated per-user data (`@login_required`). User A cannot view or alter User B's vouchers.
2. **Dashboard & Budget Tracking**:
   - **4 Ledger Cards**: Monthly Budget, Total Spent, Remaining Balance (Net Reserve), and **Daily Safe-to-Spend Allowance** (`Remaining Budget / Days Left in Month`).
   - **Pastel Budget Meter**: Smoothly transitions from Sage Green (<60%) $\to$ Warm Ochre (60-85%) $\to$ Dusty Rose (>85%).
3. **Student Categories**:
   - 🍎 Groceries & Food
   - 🏠 Campus Housing / Rent
   - 📚 Books & Supplies
   - 🚌 Transport & Transit
   - ☕ Coffee & Leisure
   - 📱 Tech & Subscriptions
   - 🏷️ Miscellaneous
4. **General Accounting Ledger (CRUD)**:
   - Full Create, Read, Update, Delete for expenses.
   - Filter by student category, search by payee/notes, and month-by-month historical selector.
   - Double-underline accounting total summary row.
5. **Visual Analytics (Chart.js)**:
   - Category Breakdown Doughnut Chart with soft pastel palette and typewriter legends.
   - Cumulative Expenditure Pace line chart tracking daily spend vs. prorated monthly budget ceiling.
6. **Instant Demo Seeder**:
   - Includes management command and one-click dashboard button to instantly populate a sample student ledger.

---

## 🚀 Quick Start Guide

### 1. Launch the Server
From the project folder:
```powershell
python manage.py runserver
```
Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 2. Pre-Configured Demo Account
You can log in directly with the seeded demo student account:
- **Scholar ID / Username**: `student`
- **Secret Passcode**: `scholar123`

Or click **"Enrol for a Scholar Card"** to create a fresh student account.

### 3. Running Automated Tests
```powershell
python manage.py test
```

### 4. Re-seeding Demo Data
```powershell
python manage.py seed_demo_data --username student
```

---

## 🌐 Deploying to Render (render.com)

The project is already fully configured for Render with:
- `render.yaml` (1-click Blueprint configuration)
- `build.sh` (automatic dependency installation, migrations, static asset collection, and demo data seeding)
- `Procfile` (`web: gunicorn config.wsgi:application`)
- `requirements.txt` (with Gunicorn, WhiteNoise, and database adapters)
- Automatic PostgreSQL (`DATABASE_URL`) or SQLite fallback support

### Option A: 1-Click Render Blueprint (Recommended)
1. Push your repository to **GitHub** or **GitLab**.
2. Go to your [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** $\to$ **Blueprint**.
4. Connect your repository.
5. Render will automatically read `render.yaml` and configure:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`
   - Environment variables (`PYTHON_VERSION`, `DEBUG`, `ALLOWED_HOSTS`, etc.)
6. Click **Apply**. Your app will build and go live at `https://<your-app-name>.onrender.com`!

### Option B: Manual Web Service Setup
1. On [Render](https://dashboard.render.com/), click **New +** $\to$ **Web Service**.
2. Connect your GitHub repository.
3. Choose the following settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `DJANGO_SECRET_KEY`: *(click Generate or enter a random string)*
   - `CSRF_TRUSTED_ORIGINS`: `https://*.onrender.com`
5. Click **Create Web Service**.

