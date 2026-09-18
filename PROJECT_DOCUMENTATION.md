# MCA Project Documentation — Smart Personal Expense Tracker

## Abstract
Smart Personal Expense Tracker is a Python desktop application that helps users record income, expenses and transfers, manage accounts and budgets, analyze spending patterns, and generate financial reports. MySQL provides persistent relational storage while SQL queries, Pandas and Matplotlib provide analysis and visualization.

## Modules
1. Authentication
2. Dashboard
3. Expense/Income/Transfer Management
4. Account Management
5. Category Management through seeded user categories
6. Monthly Budget
7. Analytics and Charts
8. Smart Insights
9. Report Generation

## ER Relationship Summary
- One user has many accounts.
- One user has many categories.
- One user has many transactions.
- An account can be referenced by many transactions.
- A category can be referenced by many income/expense transactions.
- A user can have one monthly budget per month.
- A budget can have multiple category budget allocations.

## Functional Requirements
- User registration/login
- CRUD for transactions
- Account management
- Budget management
- Search/filter
- Analytics
- Report export

## Non-functional Requirements
- Usability
- Security
- Reliability
- Maintainability
- Database integrity

## Future Scope
- Recurring expenses
- Receipt image attachment
- Cloud backup
- Mobile application
- AI-based expense forecasting
- Bank statement import
