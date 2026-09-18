from pathlib import Path
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

REPORT_DIR = Path("generated_reports")
REPORT_DIR.mkdir(exist_ok=True)

def transaction_dataframe(db, user_id, start_date, end_date):
    rows = db.fetchall(
        """SELECT t.transaction_date Date,
                  t.transaction_type Type,
                  COALESCE(c.name,'Transfer') Category,
                  COALESCE(a.account_name,'Multiple Accounts') Account,
                  t.amount Amount,
                  t.description Description,
                  t.payment_method Payment_Method
           FROM transactions t
           LEFT JOIN categories c ON c.id=t.category_id
           LEFT JOIN accounts a ON a.id=t.account_id
           WHERE t.user_id=%s AND t.transaction_date BETWEEN %s AND %s
           ORDER BY t.transaction_date DESC, t.id DESC""",
        (user_id, start_date, end_date),
    )
    return pd.DataFrame(rows)

def export_csv(df):
    path = REPORT_DIR / f"transactions_{datetime.now():%Y%m%d_%H%M%S}.csv"
    df.to_csv(path, index=False)
    return path

def export_excel(df):
    path = REPORT_DIR / f"transactions_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df.to_excel(path, index=False)
    return path

def export_pdf(df, title="Personal Finance Report"):
    path = REPORT_DIR / f"finance_report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    story = [Paragraph(title, title_style), Spacer(1, 12)]

    if df.empty:
        story.append(Paragraph("No transactions found for the selected period.", styles["BodyText"]))
    else:
        income = df.loc[df["Type"] == "INCOME", "Amount"].sum()
        expense = df.loc[df["Type"] == "EXPENSE", "Amount"].sum()
        story.append(Paragraph(f"Total Income: ₹{income:,.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Total Expenses: ₹{expense:,.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Net Balance: ₹{income-expense:,.2f}", styles["BodyText"]))
        story.append(Spacer(1, 12))
        display = df.head(30).copy()
        data = [list(display.columns)]
        for row in display.itertuples(index=False):
            data.append([str(x)[:35] for x in row])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#FFD83D")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.black),
            ("GRID",(0,0),(-1,-1),0.4,colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),7),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(table)
    doc.build(story)
    return path
