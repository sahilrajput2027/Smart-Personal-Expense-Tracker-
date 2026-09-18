import pandas as pd
import numpy as np

def category_expenses(db, user_id, start_date, end_date):
    rows = db.fetchall(
        """SELECT c.name AS category, SUM(t.amount) AS total
           FROM transactions t
           JOIN categories c ON c.id=t.category_id
           WHERE t.user_id=%s AND t.transaction_type='EXPENSE'
             AND t.transaction_date BETWEEN %s AND %s
           GROUP BY c.name ORDER BY total DESC""",
        (user_id, start_date, end_date),
    )
    return pd.DataFrame(rows)

def monthly_summary(db, user_id, start_date, end_date):
    rows = db.fetchall(
        """SELECT DATE_FORMAT(transaction_date,'%%Y-%%m') AS month,
                  SUM(CASE WHEN transaction_type='INCOME' THEN amount ELSE 0 END) income,
                  SUM(CASE WHEN transaction_type='EXPENSE' THEN amount ELSE 0 END) expense
           FROM transactions
           WHERE user_id=%s AND transaction_date BETWEEN %s AND %s
           GROUP BY DATE_FORMAT(transaction_date,'%%Y-%%m')
           ORDER BY month""",
        (user_id, start_date, end_date),
    )
    return pd.DataFrame(rows)

def daily_expenses(db, user_id, start_date, end_date):
    rows = db.fetchall(
        """SELECT transaction_date AS day, SUM(amount) AS expense
           FROM transactions
           WHERE user_id=%s AND transaction_type='EXPENSE'
             AND transaction_date BETWEEN %s AND %s
           GROUP BY transaction_date ORDER BY transaction_date""",
        (user_id, start_date, end_date),
    )
    return pd.DataFrame(rows)

def build_insights(db, user_id, year, month):
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year+1:04d}-01-01"
    else:
        end = f"{year:04d}-{month+1:02d}-01"

    current = db.fetchone(
        """SELECT
             COALESCE(SUM(CASE WHEN transaction_type='INCOME' THEN amount END),0) income,
             COALESCE(SUM(CASE WHEN transaction_type='EXPENSE' THEN amount END),0) expense
           FROM transactions
           WHERE user_id=%s AND transaction_date >= %s AND transaction_date < %s""",
        (user_id, start, end),
    ) or {"income": 0, "expense": 0}

    top = db.fetchone(
        """SELECT c.name, SUM(t.amount) total
           FROM transactions t JOIN categories c ON c.id=t.category_id
           WHERE t.user_id=%s AND t.transaction_type='EXPENSE'
             AND t.transaction_date >= %s AND t.transaction_date < %s
           GROUP BY c.name ORDER BY total DESC LIMIT 1""",
        (user_id, start, end),
    )

    previous = db.fetchone(
        """SELECT COALESCE(SUM(amount),0) expense
           FROM transactions
           WHERE user_id=%s AND transaction_type='EXPENSE'
             AND transaction_date >= DATE_SUB(%s, INTERVAL 1 MONTH)
             AND transaction_date < %s""",
        (user_id, start, start),
    ) or {"expense": 0}

    budget = db.fetchone(
        "SELECT COALESCE(SUM(amount),0) amount FROM budgets WHERE user_id=%s AND budget_month=%s",
        (user_id, f"{year:04d}-{month:02d}-01"),
    ) or {"amount": 0}

    income = float(current["income"] or 0)
    expense = float(current["expense"] or 0)
    prev_expense = float(previous["expense"] or 0)
    budget_amount = float(budget["amount"] or 0)

    insights = []
    if top:
        insights.append(f"Highest spending category: {top['name']} (₹{float(top['total']):,.2f}).")
    if prev_expense > 0:
        change = ((expense - prev_expense) / prev_expense) * 100
        if change >= 0:
            insights.append(f"You spent {change:.1f}% more than the previous month.")
        else:
            insights.append(f"You spent {abs(change):.1f}% less than the previous month.")
    if budget_amount > 0:
        pct = expense / budget_amount * 100
        insights.append(f"You have used {pct:.1f}% of your monthly budget.")
        if pct >= 100:
            insights.append("Warning: your monthly budget has been exceeded.")
        elif pct >= 80:
            insights.append("Caution: you are close to your monthly budget limit.")
    days_elapsed = max(pd.Timestamp.today().day, 1)
    avg = expense / days_elapsed
    insights.append(f"Average daily spending so far: ₹{avg:,.2f}.")
    if income > 0:
        savings_rate = ((income - expense) / income) * 100
        insights.append(f"Current savings rate: {savings_rate:.1f}%.")
    return insights
