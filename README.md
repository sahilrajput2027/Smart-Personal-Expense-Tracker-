# Smart Personal Expense Tracker

A Python desktop application for personal finance management, designed as an MCA college project.

## Technology
- Python 3
- Tkinter / ttk
- MySQL + SQL
- Pandas + NumPy
- Matplotlib
- ReportLab
- openpyxl
- python-dotenv

No HTML, CSS, JavaScript, Flask, or Django is used.

## Features
- Login and registration with password hashing
- Expense, income, and transfer management
- Accounts and balances
- 28+ expense categories
- Monthly and category budgets
- Budget warnings
- Dashboard with financial KPIs
- Monthly/category/daily analytics
- Smart spending insights
- CSV, Excel and PDF reports
- Search/filter/edit/delete transactions
- MySQL relational database

## Setup

1. Install Python 3.11+.
2. Install MySQL Server and MySQL Workbench.
3. Copy `.env.example` to `.env`.
4. Put your MySQL credentials in `.env`.
5. Open a terminal in this project folder.
6. Run `python database_setup.py` once to create the database and all tables.
7. Run:
   ```
   python -m pip install -r requirements.txt
   ```
8. Start:
   ```
   python main.py
   ```

The app creates default categories for each new user.

## Suggested demo flow
Register -> Add Account -> Add Income -> Add Expenses -> Set Budget -> Dashboard -> Charts -> Reports -> Export PDF/Excel.

## Project structure
```
smart_personal_expense_tracker/
├── main.py
├── db.py
├── analytics.py
├── reports.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── database/
│   └── database.sql
├── generated_reports/
└── charts/
```

## College project title
**Smart Personal Expense Tracker using Python and MySQL**

## Important
This is a personal finance tracking application, not a banking application. It does not connect to real bank accounts or process real payments.
