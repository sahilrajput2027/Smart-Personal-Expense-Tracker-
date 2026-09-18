import os
import hashlib
import hmac
from datetime import date, datetime
import calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from db import Database
from database_setup import initialize_database
from analytics import (
    category_expenses,
    monthly_summary,
    daily_expenses,
    build_insights
)
from reports import (
    transaction_dataframe,
    export_csv,
    export_excel,
    export_pdf
)


# ============================================================
# COLORS
# ============================================================

BG = "#F7F7F7"
YELLOW = "#FFD83D"
DARK = "#171717"
GREY = "#6B6B6B"
WHITE = "#FFFFFF"
GREEN = "#35B86B"
RED = "#E45555"
BLUE = "#5B8DEF"


# ============================================================
# EXPENSE CATEGORIES
# ============================================================

EXPENSE_CATEGORIES = [
    ("Stationery", "📚"),
    ("Rent", "🏠"),
    ("Salon", "💇"),
    ("Drinks", "🥤"),
    ("Investment", "📈"),
    ("Shopping", "🛒"),
    ("Food", "🍽"),
    ("Phone", "📱"),
    ("Entertainment", "🎬"),
    ("Education", "🎓"),
    ("Beauty", "💄"),
    ("Sports", "🏊"),
    ("Social", "👥"),
    ("Transportation", "🚌"),
    ("Clothing", "👕"),
    ("Car", "🚗"),
    ("Alcohol", "🍷"),
    ("Electronics", "🔌"),
    ("Travel", "✈"),
    ("Health", "⚕"),
    ("Pets", "🐾"),
    ("Repairs", "🔧"),
    ("Housing", "🧱"),
    ("Home", "🏡"),
    ("Gifts", "🎁"),
    ("Donations", "♥"),
    ("Lottery", "⑧"),
    ("Snacks", "🧁")
]


# ============================================================
# INCOME CATEGORIES
# ============================================================

INCOME_CATEGORIES = [
    ("Salary", "💼"),
    ("Freelance", "💻"),
    ("Business", "🏢"),
    ("Interest", "💰"),
    ("Investment Returns", "📈"),
    ("Bonus", "🎁"),
    ("Gift", "🎀"),
    ("Other Income", "＋")
]


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):
    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        180000
    )

    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(":")

        test = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            180000
        )

        return hmac.compare_digest(
            test.hex(),
            digest_hex
        )

    except Exception:
        return False


# ============================================================
# MONEY FORMAT / CURRENCY
# ============================================================

CURRENCY_CONFIG = {
    "Indian Rupee (₹)": {"symbol": "₹", "rate": 1.0},
    "US Dollar ($)": {"symbol": "$", "rate": 0.0117},
    "Euro (€)": {"symbol": "€", "rate": 0.0099},
    "British Pound (£)": {"symbol": "£", "rate": 0.0086},
}

ACTIVE_CURRENCY = "Indian Rupee (₹)"
ACTIVE_CURRENCY_SYMBOL = "₹"
ACTIVE_CURRENCY_RATE = 1.0

def money(value):
    converted = float(value or 0) * ACTIVE_CURRENCY_RATE
    return f"{ACTIVE_CURRENCY_SYMBOL}{converted:,.2f}"


# ============================================================
# APPLICATION
# ============================================================

class App(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("Smart Personal Expense Tracker")

        self.geometry("1180x760")

        self.minsize(1000, 680)

        self.configure(bg=BG)

        # Database
        self.db = Database()
        initialize_database()
        self.ensure_feature_tables()

        # Logged-in user
        self.user = None

        # Currency preferences
        self.currency_name = "Indian Rupee (₹)"
        self.currency_symbol = "₹"
        self.currency_rate = 1.0

        # Financial alert state for the current application session.
        self._shown_alerts = set()
        self._alert_job = None

        # ttk styling
        self.style = ttk.Style(self)

        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(
            "Treeview",
            rowheight=34,
            font=("Segoe UI", 10),
            background=WHITE,
            fieldbackground=WHITE
        )

        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            background="#EFEFEF"
        )

        self.show_login()


    # ========================================================
    # CLEAR WINDOW
    # ========================================================

    def clear(self):

        for widget in self.winfo_children():
            widget.destroy()


    # ========================================================
    # LOGIN PAGE
    # ========================================================

    def show_login(self):

        if self._alert_job is not None:
            try:
                self.after_cancel(self._alert_job)
            except Exception:
                pass
            self._alert_job = None

        self.user = None
        self._shown_alerts.clear()
        self.clear()

        frame = tk.Frame(
            self,
            bg=YELLOW
        )

        frame.pack(
            fill="both",
            expand=True
        )

        # Login card
        card = tk.Frame(
            frame,
            bg=WHITE
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=500,
            height=620
        )


        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        tk.Label(
            card,
            text="₹",
            font=("Segoe UI", 42, "bold"),
            fg=DARK,
            bg=YELLOW,
            width=3
        ).pack(
            pady=(32, 8)
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        tk.Label(
            card,
            text="Smart Personal",
            font=("Segoe UI", 24, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack()


        tk.Label(
            card,
            text="Expense Tracker",
            font=("Segoe UI", 17),
            bg=WHITE,
            fg=GREY
        ).pack(
            pady=(0, 25)
        )


        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        form = tk.Frame(
            card,
            bg=WHITE
        )

        form.pack(
            fill="x",
            padx=55
        )


        # Email
        tk.Label(
            form,
            text="Email",
            bg=WHITE,
            fg=GREY,
            font=("Segoe UI", 10)
        ).pack(
            anchor="w"
        )


        email = ttk.Entry(
            form,
            font=("Segoe UI", 12)
        )

        email.pack(
            fill="x",
            ipady=7,
            pady=(3, 14)
        )


        # Password
        tk.Label(
            form,
            text="Password",
            bg=WHITE,
            fg=GREY,
            font=("Segoe UI", 10)
        ).pack(
            anchor="w"
        )


        pwd = ttk.Entry(
            form,
            show="•",
            font=("Segoe UI", 12)
        )

        pwd.pack(
            fill="x",
            ipady=7,
            pady=(3, 18)
        )


        # ----------------------------------------------------
        # LOGIN FUNCTION
        # ----------------------------------------------------

        def login():

            try:

                email_value = email.get().strip().lower()
                password_value = pwd.get()

                if not email_value or not password_value:

                    messagebox.showwarning(
                        "Login",
                        "Please enter email and password."
                    )

                    return


                user = self.db.fetchone(
                    """
                    SELECT *
                    FROM users
                    WHERE email=%s
                    """,
                    (email_value,)
                )


                if user and verify_password(
                    password_value,
                    user["password_hash"]
                ):

                    self.user = user
                    self.load_currency_setting()

                    self.show_main()
                    self.after(300, self.check_financial_alerts)

                else:

                    messagebox.showerror(
                        "Login Failed",
                        "Incorrect email or password."
                    )


            except Exception as e:

                self.db_error(e)


        # Login button
        self.yellow_button(
            form,
            "LOGIN",
            login
        ).pack(
            fill="x",
            ipady=9
        )


        # ----------------------------------------------------
        # DIVIDER
        # ----------------------------------------------------

        tk.Frame(
            card,
            bg="#E6E6E6",
            height=1
        ).pack(
            fill="x",
            padx=55,
            pady=(25, 15)
        )


        # ----------------------------------------------------
        # SIGN UP SECTION
        # ----------------------------------------------------

        tk.Label(
            card,
            text="Don't have an account?",
            bg=WHITE,
            fg=GREY,
            font=("Segoe UI", 10)
        ).pack()


        tk.Button(
            card,
            text="CREATE A NEW ACCOUNT",
            command=self.show_register,
            bg=WHITE,
            fg="#4A65A8",
            activebackground=WHITE,
            activeforeground=DARK,
            bd=0,
            font=("Segoe UI Semibold", 11, "underline"),
            cursor="hand2"
        ).pack(
            pady=(8, 5)
        )


    # ========================================================
    # REGISTER PAGE
    # ========================================================

    def show_register(self):

        self.clear()

        frame = tk.Frame(
            self,
            bg=YELLOW
        )

        frame.pack(
            fill="both",
            expand=True
        )


        card = tk.Frame(
            frame,
            bg=WHITE
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=500,
            height=590
        )


        # Title
        tk.Label(
            card,
            text="Create Account",
            font=("Segoe UI", 25, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(
            pady=(35, 25)
        )


        form = tk.Frame(
            card,
            bg=WHITE
        )

        form.pack(
            fill="x",
            padx=55
        )


        entries = {}


        # Registration fields
        fields = [
            ("Full Name", "name", None),
            ("Email", "email", None),
            ("Password", "password", "•"),
            ("Confirm Password", "confirm", "•")
        ]


        for label, key, show in fields:

            tk.Label(
                form,
                text=label,
                bg=WHITE,
                fg=GREY,
                font=("Segoe UI", 10)
            ).pack(
                anchor="w"
            )


            entry = ttk.Entry(
                form,
                show=show,
                font=("Segoe UI", 12)
            )


            entry.pack(
                fill="x",
                ipady=7,
                pady=(3, 12)
            )


            entries[key] = entry


        # ----------------------------------------------------
        # REGISTER FUNCTION
        # ----------------------------------------------------

        def register():

            name = entries["name"].get().strip()

            email = entries["email"].get().strip().lower()

            password = entries["password"].get()

            confirm = entries["confirm"].get()


            # Empty fields
            if not name or not email or not password:

                messagebox.showwarning(
                    "Missing Data",
                    "Please complete all fields."
                )

                return


            # Email validation
            if "@" not in email or "." not in email:

                messagebox.showwarning(
                    "Invalid Email",
                    "Please enter a valid email address."
                )

                return


            # Password validation
            if len(password) < 6:

                messagebox.showwarning(
                    "Password",
                    "Password must contain at least 6 characters."
                )

                return


            # Confirm password
            if password != confirm:

                messagebox.showwarning(
                    "Password",
                    "Passwords do not match."
                )

                return


            try:

                # Check existing email
                existing = self.db.fetchone(
                    """
                    SELECT id
                    FROM users
                    WHERE email=%s
                    """,
                    (email,)
                )


                if existing:

                    messagebox.showerror(
                        "Registration",
                        "Email already exists."
                    )

                    return


                # Create user
                uid = self.db.execute(
                    """
                    INSERT INTO users
                    (
                        name,
                        email,
                        password_hash
                    )
                    VALUES(%s,%s,%s)
                    """,
                    (
                        name,
                        email,
                        hash_password(password)
                    )
                )


                # Add default categories
                self.seed_categories(uid)


                messagebox.showinfo(
                    "Success",
                    "Account created successfully!\n\n"
                    "You can now log in."
                )


                self.show_login()


            except Exception as e:

                self.db_error(e)


        # Create account button
        self.yellow_button(
            form,
            "CREATE ACCOUNT",
            register
        ).pack(
            fill="x",
            ipady=8,
            pady=(8, 5)
        )


        # Back button
        tk.Button(
            card,
            text="← Back to Login",
            command=self.show_login,
            bg=WHITE,
            fg=GREY,
            activebackground=WHITE,
            bd=0,
            font=("Segoe UI", 10),
            cursor="hand2"
        ).pack(
            pady=10
        )


    # ========================================================
    # CREATE DEFAULT CATEGORIES
    # ========================================================

    def seed_categories(self, uid):

        rows = []

        # Expense categories
        for name, icon in EXPENSE_CATEGORIES:

            rows.append(
                (
                    uid,
                    name,
                    "EXPENSE",
                    icon,
                    YELLOW
                )
            )

        # Income categories
        for name, icon in INCOME_CATEGORIES:

            rows.append(
                (
                    uid,
                    name,
                    "INCOME",
                    icon,
                    YELLOW
                )
            )

        self.db.executemany(
            """
            INSERT INTO categories
            (
                user_id,
                name,
                category_type,
                icon,
                color
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            rows
        )


    # ========================================================
    # YELLOW BUTTON
    # ========================================================

    def yellow_button(
        self,
        parent,
        text,
        command
    ):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=YELLOW,
            fg=DARK,
            activebackground="#F2C900",
            activeforeground=DARK,
            bd=0,
            font=("Segoe UI Semibold", 11),
            cursor="hand2"
        )


    # ========================================================
    # MAIN SCREEN
    # ========================================================

    def load_currency_setting(self):

        global ACTIVE_CURRENCY, ACTIVE_CURRENCY_SYMBOL, ACTIVE_CURRENCY_RATE

        try:
            row = self.db.fetchone(
                """
                SELECT setting_value
                FROM app_settings
                WHERE user_id=%s AND setting_key='currency'
                """,
                (self.user["id"],)
            )
            name = row["setting_value"] if row else "Indian Rupee (₹)"
        except Exception:
            name = "Indian Rupee (₹)"

        config = CURRENCY_CONFIG.get(name, CURRENCY_CONFIG["Indian Rupee (₹)"])
        self.currency_name = name
        self.currency_symbol = config["symbol"]
        self.currency_rate = config["rate"]

        ACTIVE_CURRENCY = name
        ACTIVE_CURRENCY_SYMBOL = self.currency_symbol
        ACTIVE_CURRENCY_RATE = self.currency_rate

    def apply_currency_setting(self, name):

        global ACTIVE_CURRENCY, ACTIVE_CURRENCY_SYMBOL, ACTIVE_CURRENCY_RATE

        config = CURRENCY_CONFIG.get(
            name,
            CURRENCY_CONFIG["Indian Rupee (₹)"]
        )
        self.currency_name = name
        self.currency_symbol = config["symbol"]
        self.currency_rate = config["rate"]

        ACTIVE_CURRENCY = name
        ACTIVE_CURRENCY_SYMBOL = self.currency_symbol
        ACTIVE_CURRENCY_RATE = self.currency_rate

    def amount_to_base(self, value):
        """Convert an amount entered in the selected currency to INR."""
        return float(value or 0) / self.currency_rate


    def show_main(self):

        self.clear()


        # Sidebar
        self.sidebar = tk.Frame(
            self,
            bg=WHITE,
            width=210
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)


        # Content
        self.content = tk.Frame(
            self,
            bg=BG
        )

        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )


        # Logo
        tk.Label(
            self.sidebar,
            text="₹",
            font=("Segoe UI", 28, "bold"),
            bg=YELLOW,
            fg=DARK,
            width=3
        ).pack(
            pady=(25, 8)
        )


        tk.Label(
            self.sidebar,
            text="SMART EXPENSE",
            font=("Segoe UI Semibold", 14),
            bg=WHITE,
            fg=DARK
        ).pack()


        tk.Label(
            self.sidebar,
            text="Personal Finance",
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=GREY
        ).pack(
            pady=(0, 25)
        )


        # Navigation buttons
        navigation = [
            ("⌂  Home", self.dashboard),
            ("＋  Add Transaction", self.add_transaction),
            ("▦  Transactions", self.transactions),
            ("◔  Charts & Analytics", self.charts),
            ("▣  Budgets", self.budgets),
            ("🎯  Financial Goals", self.financial_goals),
            ("🔔  Reminders", self.reminders),
            ("⚙  Settings", self.settings),
            ("▤  Reports", self.reports),
            ("◉  Accounts", self.accounts),
            ("⚙  Profile", self.profile)
        ]


        for label, method in navigation:

            tk.Button(
                self.sidebar,
                text=label,
                command=method,
                anchor="w",
                bg=WHITE,
                fg=DARK,
                activebackground="#FFF4B8",
                bd=0,
                font=("Segoe UI", 10),
                padx=20,
                pady=11
            ).pack(
                fill="x"
            )


        # Logout
        tk.Button(
            self.sidebar,
            text="↪  Logout",
            command=self.show_login,
            anchor="w",
            bg=WHITE,
            fg=RED,
            activebackground="#FFECEC",
            bd=0,
            font=("Segoe UI", 10),
            padx=20,
            pady=11
        ).pack(
            side="bottom",
            fill="x"
        )


        self.dashboard()


    # ========================================================
    # HEADER
    # ========================================================

    def header(
        self,
        title,
        subtitle=""
    ):

        for widget in self.content.winfo_children():
            widget.destroy()


        top = tk.Frame(
            self.content,
            bg=YELLOW,
            height=92
        )

        top.pack(
            fill="x"
        )

        top.pack_propagate(False)


        tk.Label(
            top,
            text=title,
            font=("Segoe UI", 25, "bold"),
            bg=YELLOW,
            fg=DARK
        ).pack(
            anchor="w",
            padx=30,
            pady=(18, 0)
        )


        if subtitle:

            tk.Label(
                top,
                text=subtitle,
                font=("Segoe UI", 10),
                bg=YELLOW,
                fg="#5A4E00"
            ).pack(
                anchor="w",
                padx=31
            )


        body = tk.Frame(
            self.content,
            bg=BG
        )

        body.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=22
        )


        return body


    # ========================================================
    # DASHBOARD CARD
    # ========================================================

    def card(
        self,
        parent,
        title,
        value,
        accent=YELLOW
    ):

        frame = tk.Frame(
            parent,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )


        tk.Frame(
            frame,
            bg=accent,
            width=6
        ).pack(
            side="left",
            fill="y"
        )


        inside = tk.Frame(
            frame,
            bg=WHITE
        )

        inside.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=12
        )


        tk.Label(
            inside,
            text=title.upper(),
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=GREY
        ).pack(
            anchor="w"
        )


        tk.Label(
            inside,
            text=value,
            font=("Segoe UI", 19, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(
            anchor="w",
            pady=(5, 0)
        )


        return frame


    # ========================================================
    # DASHBOARD
    # ========================================================

    def dashboard(self):

        body = self.header(
            f"Good day, {self.user['name'].split()[0]} 👋",
            "Your personal financial overview"
        )


        now = date.today()

        start = now.replace(
            day=1
        )


        # Total income
        income = self.db.fetchone(
            """
            SELECT COALESCE(SUM(amount),0) total
            FROM transactions
            WHERE user_id=%s
            AND transaction_type='INCOME'
            """,
            (self.user["id"],)
        )["total"]


        # Total expenses
        expense = self.db.fetchone(
            """
            SELECT COALESCE(SUM(amount),0) total
            FROM transactions
            WHERE user_id=%s
            AND transaction_type='EXPENSE'
            """,
            (self.user["id"],)
        )["total"]


        # Balance
        balance = self.total_balance()


        # Monthly income
        month_inc = self.db.fetchone(
            """
            SELECT COALESCE(SUM(amount),0) total
            FROM transactions
            WHERE user_id=%s
            AND transaction_type='INCOME'
            AND transaction_date>=%s
            """,
            (
                self.user["id"],
                start
            )
        )["total"]


        # Monthly expense
        month_exp = self.db.fetchone(
            """
            SELECT COALESCE(SUM(amount),0) total
            FROM transactions
            WHERE user_id=%s
            AND transaction_type='EXPENSE'
            AND transaction_date>=%s
            """,
            (
                self.user["id"],
                start
            )
        )["total"]


        # Cards
        row = tk.Frame(
            body,
            bg=BG
        )

        row.pack(
            fill="x"
        )


        cards = [
            (
                "Total Balance",
                money(balance),
                YELLOW
            ),
            (
                "Total Income",
                money(income),
                GREEN
            ),
            (
                "Total Expenses",
                money(expense),
                RED
            ),
            (
                "This Month",
                money(month_exp),
                BLUE
            )
        ]


        for title, value, accent in cards:

            card = self.card(
                row,
                title,
                value,
                accent
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 12)
            )


        # Lower section
        lower = tk.Frame(
            body,
            bg=BG
        )

        lower.pack(
            fill="both",
            expand=True,
            pady=18
        )


        # Recent transactions
        left = tk.Frame(
            lower,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )

        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 9)
        )


        tk.Label(
            left,
            text="Recent Transactions",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=18,
            pady=15
        )


        tree = self.make_tree(
            left,
            (
                "Date",
                "Type",
                "Category",
                "Account",
                "Amount"
            ),
            (
                100,
                100,
                170,
                150,
                110
            )
        )


        rows = self.db.fetchall(
            """
            SELECT
                t.transaction_date,
                t.transaction_type,
                COALESCE(c.name,'Transfer') cat,
                COALESCE(a.account_name,'Multiple') acc,
                t.amount
            FROM transactions t
            LEFT JOIN categories c
                ON c.id=t.category_id
            LEFT JOIN accounts a
                ON a.id=t.account_id
            WHERE t.user_id=%s
            ORDER BY t.id DESC
            LIMIT 8
            """,
            (self.user["id"],)
        )


        for row_data in rows:

            tree.insert(
                "",
                "end",
                values=(
                    row_data["transaction_date"],
                    row_data["transaction_type"],
                    row_data["cat"],
                    row_data["acc"],
                    money(row_data["amount"])
                )
            )


        # Smart insights
        right = tk.Frame(
            lower,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )

        right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(9, 0)
        )


        tk.Label(
            right,
            text="Smart Insights",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=18,
            pady=15
        )


        insights = build_insights(
            self.db,
            self.user["id"],
            now.year,
            now.month
        )


        if not insights:

            tk.Label(
                right,
                text="No insights available yet.\n"
                     "Add some transactions to generate insights.",
                wraplength=390,
                justify="left",
                font=("Segoe UI", 10),
                bg=WHITE,
                fg=GREY
            ).pack(
                anchor="w",
                padx=22,
                pady=10
            )


        for text in insights[:6]:

            tk.Label(
                right,
                text="• " + text,
                wraplength=390,
                justify="left",
                font=("Segoe UI", 10),
                bg=WHITE,
                fg=DARK
            ).pack(
                anchor="w",
                padx=22,
                pady=8
            )


    # ========================================================
    # TOTAL BALANCE
    # ========================================================

    def total_balance(self):

        rows = self.db.fetchall(
            """
            SELECT id, opening_balance
            FROM accounts
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )


        total = sum(
            float(row["opening_balance"])
            for row in rows
        )


        row = self.db.fetchone(
            """
            SELECT COALESCE(
                SUM(
                    CASE
                        WHEN transaction_type='INCOME'
                            THEN amount

                        WHEN transaction_type='EXPENSE'
                            THEN -amount

                        ELSE 0
                    END
                ),0
            ) x
            FROM transactions
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )


        total += float(
            row["x"] or 0
        )


        transfers = self.db.fetchone(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN from_account_id IS NOT NULL
                                THEN -amount
                            ELSE 0
                        END
                    ),0
                ) outflow,

                COALESCE(
                    SUM(
                        CASE
                            WHEN to_account_id IS NOT NULL
                                THEN amount
                            ELSE 0
                        END
                    ),0
                ) inflow

            FROM transactions
            WHERE user_id=%s
            AND transaction_type='TRANSFER'
            """,
            (self.user["id"],)
        )


        total += float(
            transfers["outflow"] or 0
        )

        total += float(
            transfers["inflow"] or 0
        )


        return total


    # ========================================================
    # TREEVIEW
    # ========================================================

    def make_tree(
        self,
        parent,
        columns,
        widths
    ):

        wrapper = tk.Frame(
            parent,
            bg=WHITE
        )

        wrapper.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 15)
        )


        tree = ttk.Treeview(
            wrapper,
            columns=columns,
            show="headings"
        )


        for column, width in zip(
            columns,
            widths
        ):

            tree.heading(
                column,
                text=column
            )

            tree.column(
                column,
                width=width,
                anchor="w"
            )


        scrollbar = ttk.Scrollbar(
            wrapper,
            orient="vertical",
            command=tree.yview
        )


        tree.configure(
            yscrollcommand=scrollbar.set
        )


        tree.pack(
            side="left",
            fill="both",
            expand=True
        )


        scrollbar.pack(
            side="right",
            fill="y"
        )


        return tree


    # ========================================================
    # ADD TRANSACTION
    # ========================================================

    def add_transaction(self):

        body = self.header(
            "Add Transaction",
            "Record an expense, income or transfer"
        )

        tabs = tk.Frame(body, bg=BG)
        tabs.pack(fill="x", pady=(0, 15))

        # Scrollable transaction area
        form_area = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        form_area.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            form_area,
            bg=WHITE,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            form_area,
            orient="vertical",
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_content = tk.Frame(canvas, bg=WHITE)
        window_id = canvas.create_window(
            (0, 0),
            window=scroll_content,
            anchor="nw"
        )

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_content(event):
            canvas.itemconfigure(window_id, width=event.width)

        scroll_content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_content)

        def mouse_wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        def enable_mousewheel(event):
            canvas.bind_all("<MouseWheel>", mouse_wheel)

        def disable_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", enable_mousewheel)
        canvas.bind("<Leave>", disable_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def rebuild(kind):
            for widget in tabs.winfo_children():
                widget.destroy()

            for value in ["EXPENSE", "INCOME", "TRANSFER"]:
                button = tk.Button(
                    tabs,
                    text=value,
                    command=lambda x=value: rebuild(x),
                    font=("Segoe UI Semibold", 11),
                    bd=0,
                    padx=30,
                    pady=9,
                    bg=DARK if value == kind else YELLOW,
                    fg=WHITE if value == kind else DARK,
                    activebackground=DARK if value == kind else "#F2C900",
                    activeforeground=WHITE if value == kind else DARK,
                    cursor="hand2"
                )
                button.pack(side="left", padx=(0, 2))

            for widget in scroll_content.winfo_children():
                widget.destroy()

            if kind == "TRANSFER":
                self.transfer_form(scroll_content)
            else:
                self.money_form(scroll_content, kind)

            canvas.update_idletasks()
            canvas.yview_moveto(0)

        rebuild("EXPENSE")
    def money_form(self, parent, kind):

        categories = self.db.fetchall(
            """
            SELECT id,name,icon
            FROM categories
            WHERE user_id=%s
            AND category_type=%s
            ORDER BY name
            """,
            (self.user["id"], kind)
        )

        accounts = self.db.fetchall(
            """
            SELECT id,account_name
            FROM accounts
            WHERE user_id=%s
            ORDER BY account_name
            """,
            (self.user["id"],)
        )

        if not accounts:
            tk.Label(
                parent,
                text="Add an account first from Accounts.",
                font=("Segoe UI", 13),
                bg=WHITE,
                fg=RED
            ).pack(pady=35)

            self.yellow_button(
                parent,
                "OPEN ACCOUNTS",
                self.accounts
            ).pack()
            return

        top = tk.Frame(parent, bg=WHITE)
        top.pack(fill="x", padx=25, pady=20)

        tk.Label(
            top,
            text="Choose a category",
            font=("Segoe UI", 14, "bold"),
            bg=WHITE
        ).pack(anchor="w")

        selected = tk.StringVar()
        category_buttons = {}

        category_grid = tk.Frame(top, bg=WHITE)
        category_grid.pack(fill="x", pady=10)

        def select_category(name):
            selected.set(name)
            for category_name, button in category_buttons.items():
                button.configure(
                    bg=YELLOW if category_name == name else "#FFF9D8",
                    fg=DARK
                )

            selected_label.configure(
                text=f"Selected category: {name}"
            )

        for index, category in enumerate(categories):
            name = category["name"]
            icon = category["icon"]

            button = tk.Button(
                category_grid,
                text=f"{icon}  {name}",
                command=lambda x=name: select_category(x),
                bg="#FFF9D8",
                activebackground=YELLOW,
                activeforeground=DARK,
                fg=DARK,
                bd=0,
                font=("Segoe UI", 9),
                padx=10,
                pady=9,
                cursor="hand2"
            )

            button.grid(
                row=index // 4,
                column=index % 4,
                padx=5,
                pady=5,
                sticky="ew"
            )
            category_buttons[name] = button

        for column in range(4):
            category_grid.grid_columnconfigure(column, weight=1)

        def add_new_category():
            dialog = tk.Toplevel(self)
            dialog.title("Add New Category")
            dialog.configure(bg=WHITE)
            dialog.transient(self)
            dialog.grab_set()
            dialog.resizable(False, False)

            tk.Label(
                dialog,
                text=f"Add {kind.title()} Category",
                font=("Segoe UI", 16, "bold"),
                bg=WHITE,
                fg=DARK
            ).pack(padx=25, pady=(20, 15))

            form = tk.Frame(dialog, bg=WHITE)
            form.pack(fill="x", padx=25)

            new_name = tk.StringVar()
            new_icon = tk.StringVar(value="●")

            tk.Label(
                form,
                text="Category Name",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                form,
                textvariable=new_name,
                font=("Segoe UI", 11)
            ).pack(fill="x", ipady=5, pady=(3, 12))

            tk.Label(
                form,
                text="Icon / Symbol",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                form,
                textvariable=new_icon,
                font=("Segoe UI", 11)
            ).pack(fill="x", ipady=5, pady=(3, 15))

            def save_new_category():
                name = new_name.get().strip()
                icon = new_icon.get().strip() or "●"

                if not name:
                    messagebox.showwarning(
                        "Category",
                        "Enter a category name.",
                        parent=dialog
                    )
                    return

                try:
                    existing = self.db.fetchone(
                        """
                        SELECT id
                        FROM categories
                        WHERE user_id=%s
                        AND name=%s
                        AND category_type=%s
                        """,
                        (self.user["id"], name, kind)
                    )

                    if existing:
                        messagebox.showwarning(
                            "Category",
                            "This category already exists.",
                            parent=dialog
                        )
                        return

                    self.db.execute(
                        """
                        INSERT INTO categories
                        (user_id, name, category_type, icon, color)
                        VALUES(%s,%s,%s,%s,%s)
                        """,
                        (
                            self.user["id"],
                            name,
                            kind,
                            icon,
                            YELLOW
                        )
                    )

                    dialog.destroy()

                    # Rebuild this transaction form so the new
                    # category appears immediately.
                    for widget in parent.winfo_children():
                        widget.destroy()

                    self.money_form(parent, kind)

                except Exception as e:
                    self.db_error(e)

            self.yellow_button(
                dialog,
                "ADD CATEGORY",
                save_new_category
            ).pack(
                fill="x",
                padx=25,
                pady=(0, 10),
                ipady=7
            )

            ttk.Button(
                dialog,
                text="Cancel",
                command=dialog.destroy
            ).pack(pady=(0, 20))

            dialog.update_idletasks()

            x = (
                self.winfo_x()
                + (self.winfo_width() - dialog.winfo_width()) // 2
            )
            y = (
                self.winfo_y()
                + (self.winfo_height() - dialog.winfo_height()) // 2
            )

            dialog.geometry(
                f"+{max(x, 0)}+{max(y, 0)}"
            )

            dialog.bind(
                "<Return>",
                lambda event: save_new_category()
            )
            dialog.bind(
                "<Escape>",
                lambda event: dialog.destroy()
            )

        # + button for creating a category without leaving
        # the Add Transaction screen.
        add_category_button = tk.Button(
            category_grid,
            text="＋  Add New Category",
            command=add_new_category,
            bg=YELLOW,
            activebackground="#F2C900",
            activeforeground=DARK,
            fg=DARK,
            bd=0,
            font=("Segoe UI Semibold", 9),
            padx=10,
            pady=9,
            cursor="hand2"
        )

        add_category_button.grid(
            row=len(categories) // 4,
            column=len(categories) % 4,
            padx=5,
            pady=5,
            sticky="ew"
        )

        selected_label = tk.Label(
            top,
            text="No category selected",
            bg=WHITE,
            fg=GREY,
            font=("Segoe UI", 10, "italic")
        )
        selected_label.pack(anchor="w", padx=5, pady=(2, 0))

        fields = tk.Frame(parent, bg=WHITE)
        fields.pack(fill="x", padx=30, pady=5)

        amount = tk.StringVar()
        account = tk.StringVar()
        transaction_date = tk.StringVar(value=str(date.today()))
        description = tk.StringVar()
        default_method = "UPI"
        try:
            saved_method = self.db.fetchone(
                """
                SELECT setting_value
                FROM app_settings
                WHERE user_id=%s AND setting_key=%s
                """,
                (self.user["id"], "default_payment_method")
            )
            if saved_method and saved_method.get("setting_value"):
                default_method = saved_method["setting_value"]
        except Exception:
            pass
        method = tk.StringVar(value=default_method)
        notes = tk.StringVar()

        self.field(fields, f"Amount ({self.currency_symbol})", amount, 0, 0)
        self.field(fields, "Date (YYYY-MM-DD)", transaction_date, 0, 1)

        self.field(fields, "Description", description, 1, 0)

        account_box = tk.Frame(fields, bg=WHITE)
        account_box.grid(
            row=1, column=1, sticky="ew", padx=8, pady=5
        )
        tk.Label(
            account_box,
            text="Account",
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w")
        account_combo = ttk.Combobox(
            account_box,
            textvariable=account,
            values=[a["account_name"] for a in accounts],
            state="readonly"
        )
        account_combo.pack(fill="x", ipady=5, pady=(3, 0))

        notes_box = tk.Frame(fields, bg=WHITE)
        notes_box.grid(
            row=2, column=0, sticky="ew", padx=8, pady=5
        )
        tk.Label(
            notes_box,
            text="Notes",
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w")
        ttk.Entry(notes_box, textvariable=notes).pack(
            fill="x", ipady=5, pady=(3, 0)
        )

        method_box = tk.Frame(fields, bg=WHITE)
        method_box.grid(
            row=2, column=1, sticky="ew", padx=8, pady=5
        )
        tk.Label(
            method_box,
            text="Payment Method",
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w")
        ttk.Combobox(
            method_box,
            textvariable=method,
            values=[
                "UPI",
                "Cash",
                "Debit Card",
                "Credit Card",
                "Bank Transfer",
                "Other"
            ],
            state="readonly"
        ).pack(fill="x", ipady=5, pady=(3, 0))

        fields.grid_columnconfigure(0, weight=1)
        fields.grid_columnconfigure(1, weight=1)

        def save():
            try:
                amount_value = float(amount.get())

                if amount_value <= 0:
                    raise ValueError("Amount must be greater than zero.")

                if not selected.get():
                    raise ValueError("Please choose a category.")

                if not account.get():
                    raise ValueError("Please choose an account.")

                selected_category = next(
                    c for c in categories
                    if c["name"] == selected.get()
                )

                selected_account = next(
                    a for a in accounts
                    if a["account_name"] == account.get()
                )

                datetime.strptime(
                    transaction_date.get(),
                    "%Y-%m-%d"
                )

                # Store all monetary values internally in INR.
                amount_value = self.amount_to_base(amount_value)

                self.db.execute(
                    """
                    INSERT INTO transactions
                    (
                        user_id,
                        account_id,
                        category_id,
                        transaction_type,
                        amount,
                        transaction_date,
                        description,
                        payment_method,
                        notes
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        selected_account["id"],
                        selected_category["id"],
                        kind,
                        amount_value,
                        transaction_date.get(),
                        description.get(),
                        method.get(),
                        notes.get()
                    )
                )

                self.check_budget_alert()

                messagebox.showinfo(
                    "Saved",
                    "Transaction saved successfully."
                )
                self.add_transaction()

            except ValueError as e:
                messagebox.showwarning("Invalid Data", str(e))
            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            parent,
            f"SAVE {kind}",
            save
        ).pack(
            anchor="e",
            padx=30,
            pady=18,
            ipadx=20,
            ipady=7
        )
    def transfer_form(self, parent):

        accounts = self.db.fetchall(
            """
            SELECT id,account_name
            FROM accounts
            WHERE user_id=%s
            ORDER BY account_name
            """,
            (self.user["id"],)
        )

        # Transfer has no category, so the + button here creates
        # a new account instead.
        account_values = [
            a["account_name"] for a in accounts
        ]

        account_area = tk.Frame(
            parent,
            bg=WHITE
        )
        account_area.pack(
            fill="x",
            padx=30,
            pady=(20, 0)
        )

        tk.Label(
            account_area,
            text="Transfer Between Accounts",
            font=("Segoe UI", 14, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(
            side="left"
        )

        def add_new_account():

            dialog = tk.Toplevel(self)
            dialog.title("Add New Account")
            dialog.configure(bg=WHITE)
            dialog.transient(self)
            dialog.grab_set()
            dialog.resizable(False, False)

            tk.Label(
                dialog,
                text="Add New Account",
                font=("Segoe UI", 16, "bold"),
                bg=WHITE,
                fg=DARK
            ).pack(
                padx=25,
                pady=(20, 15)
            )

            form = tk.Frame(
                dialog,
                bg=WHITE
            )
            form.pack(
                fill="x",
                padx=25
            )

            new_name = tk.StringVar()
            new_type = tk.StringVar(value="Bank Account")
            opening = tk.StringVar(value="0")

            tk.Label(
                form,
                text="Account Name",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                form,
                textvariable=new_name,
                font=("Segoe UI", 11)
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 12)
            )

            tk.Label(
                form,
                text="Account Type",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Combobox(
                form,
                textvariable=new_type,
                values=[
                    "Bank Account",
                    "Savings Account",
                    "Cash",
                    "UPI Wallet",
                    "Credit Card",
                    "Other"
                ],
                state="readonly"
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 12)
            )

            tk.Label(
                form,
                text=f"Opening Balance ({self.currency_symbol})",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                form,
                textvariable=opening,
                font=("Segoe UI", 11)
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 15)
            )

            def save_account():

                name = new_name.get().strip()

                try:
                    value = float(opening.get() or 0)

                    if not name:
                        raise ValueError(
                            "Enter an account name."
                        )

                    if value < 0:
                        raise ValueError(
                            "Opening balance cannot be negative."
                        )

                    existing = self.db.fetchone(
                        """
                        SELECT id
                        FROM accounts
                        WHERE user_id=%s AND account_name=%s
                        """,
                        (
                            self.user["id"],
                            name
                        )
                    )

                    if existing:
                        raise ValueError(
                            "This account already exists."
                        )

                    value = self.amount_to_base(value)

                    self.db.execute(
                        """
                        INSERT INTO accounts
                        (
                            user_id,
                            account_name,
                            account_type,
                            opening_balance
                        )
                        VALUES(%s,%s,%s,%s)
                        """,
                        (
                            self.user["id"],
                            name,
                            new_type.get(),
                            value
                        )
                    )

                    dialog.destroy()

                    # Rebuild the Transfer form so the new account
                    # appears immediately in both dropdowns.
                    for widget in parent.winfo_children():
                        widget.destroy()

                    self.transfer_form(parent)

                except ValueError as e:
                    messagebox.showwarning(
                        "Account",
                        str(e),
                        parent=dialog
                    )
                except Exception as e:
                    self.db_error(e)

            self.yellow_button(
                dialog,
                "ADD ACCOUNT",
                save_account
            ).pack(
                fill="x",
                padx=25,
                pady=(0, 10),
                ipady=7
            )

            ttk.Button(
                dialog,
                text="Cancel",
                command=dialog.destroy
            ).pack(
                pady=(0, 20)
            )

            dialog.bind(
                "<Return>",
                lambda event: save_account()
            )

            dialog.bind(
                "<Escape>",
                lambda event: dialog.destroy()
            )

            dialog.update_idletasks()

            x = (
                self.winfo_x()
                + (self.winfo_width() - dialog.winfo_width()) // 2
            )

            y = (
                self.winfo_y()
                + (self.winfo_height() - dialog.winfo_height()) // 2
            )

            dialog.geometry(
                f"+{max(x, 0)}+{max(y, 0)}"
            )

        add_account_button = tk.Button(
            account_area,
            text="＋  Add New Account",
            command=add_new_account,
            bg=YELLOW,
            activebackground="#F2C900",
            activeforeground=DARK,
            fg=DARK,
            bd=0,
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=8,
            cursor="hand2"
        )

        add_account_button.pack(
            side="right"
        )

        if len(accounts) < 2:

            tk.Label(
                parent,
                text="Create at least two accounts to transfer money.",
                font=("Segoe UI", 13),
                bg=WHITE,
                fg=RED
            ).pack(
                pady=35
            )

            self.yellow_button(
                parent,
                "OPEN ACCOUNTS",
                self.accounts
            ).pack()

            return

        form = tk.Frame(
            parent,
            bg=WHITE
        )

        form.pack(
            padx=60,
            pady=35,
            fill="x"
        )

        amount = tk.StringVar()
        from_account = tk.StringVar()
        to_account = tk.StringVar()
        transaction_date = tk.StringVar(
            value=str(date.today())
        )
        description = tk.StringVar()

        tk.Label(
            form,
            text="From Account",
            bg=WHITE,
            fg=GREY
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Combobox(
            form,
            textvariable=from_account,
            values=account_values,
            state="readonly",
            width=35
        ).grid(
            row=0,
            column=1,
            sticky="w",
            pady=8
        )

        tk.Label(
            form,
            text="To Account",
            bg=WHITE,
            fg=GREY
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Combobox(
            form,
            textvariable=to_account,
            values=account_values,
            state="readonly",
            width=35
        ).grid(
            row=1,
            column=1,
            sticky="w",
            pady=8
        )

        tk.Label(
            form,
            text=f"Amount ({self.currency_symbol})",
            bg=WHITE,
            fg=GREY
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=amount,
            width=38
        ).grid(
            row=2,
            column=1,
            sticky="w",
            pady=8
        )

        tk.Label(
            form,
            text="Date",
            bg=WHITE,
            fg=GREY
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=transaction_date,
            width=38
        ).grid(
            row=3,
            column=1,
            sticky="w",
            pady=8
        )

        tk.Label(
            form,
            text="Description",
            bg=WHITE,
            fg=GREY
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=description,
            width=38
        ).grid(
            row=4,
            column=1,
            sticky="w",
            pady=8
        )

        def save():

            try:

                amt = float(amount.get())

                if amt <= 0:
                    raise ValueError(
                        "Amount must be positive."
                    )

                if not from_account.get() or not to_account.get():
                    raise ValueError(
                        "Choose both accounts."
                    )

                if from_account.get() == to_account.get():
                    raise ValueError(
                        "Choose different accounts."
                    )

                datetime.strptime(
                    transaction_date.get(),
                    "%Y-%m-%d"
                )

                from_id = next(
                    a["id"]
                    for a in accounts
                    if a["account_name"] == from_account.get()
                )

                to_id = next(
                    a["id"]
                    for a in accounts
                    if a["account_name"] == to_account.get()
                )

                amt = self.amount_to_base(amt)

                self.db.transfer(
                    self.user["id"],
                    from_id,
                    to_id,
                    amt,
                    transaction_date.get(),
                    description.get()
                )

                messagebox.showinfo(
                    "Transferred",
                    "Transfer completed."
                )

                self.add_transaction()

            except ValueError as e:
                messagebox.showwarning(
                    "Transfer",
                    str(e)
                )
            except Exception as e:
                messagebox.showerror(
                    "Transfer",
                    str(e)
                )

        self.yellow_button(
            parent,
            "TRANSFER MONEY",
            save
        ).pack(
            pady=15,
            ipadx=20,
            ipady=7
        )


    def field(
        self,
        parent,
        label,
        variable,
        row,
        column
    ):

        box = tk.Frame(
            parent,
            bg=WHITE
        )


        box.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=8,
            pady=5
        )


        tk.Label(
            box,
            text=label,
            bg=WHITE,
            fg=GREY
        ).pack(
            anchor="w"
        )


        ttk.Entry(
            box,
            textvariable=variable,
            font=("Segoe UI", 10)
        ).pack(
            fill="x",
            ipady=5,
            pady=(3, 0)
        )


    # ========================================================
    # TRANSACTIONS
    # ========================================================

    def transactions(self):

        body = self.header(
            "Transactions",
            "Search, filter and delete your records"
        )


        controls = tk.Frame(
            body,
            bg=WHITE
        )

        controls.pack(
            fill="x",
            pady=(0, 12),
            ipadx=10,
            ipady=10
        )


        search = tk.StringVar()

        transaction_type = tk.StringVar(
            value="ALL"
        )


        tk.Label(
            controls,
            text="Search",
            bg=WHITE,
            fg=GREY
        ).pack(
            side="left",
            padx=(10, 5)
        )


        ttk.Entry(
            controls,
            textvariable=search,
            width=25
        ).pack(
            side="left",
            padx=5
        )


        ttk.Combobox(
            controls,
            textvariable=transaction_type,
            values=[
                "ALL",
                "EXPENSE",
                "INCOME",
                "TRANSFER"
            ],
            state="readonly",
            width=12
        ).pack(
            side="left",
            padx=5
        )


        tree = self.make_tree(
            body,
            (
                "ID",
                "Date",
                "Type",
                "Category",
                "Account",
                "Amount",
                "Description"
            ),
            (
                55,
                100,
                100,
                160,
                150,
                110,
                240
            )
        )


        def load():

            for item in tree.get_children():

                tree.delete(item)


            query = """
            SELECT
                t.id,
                t.transaction_date,
                t.transaction_type,
                COALESCE(c.name,'Transfer') cat,
                COALESCE(a.account_name,'Multiple') acc,
                t.amount,
                t.description

            FROM transactions t

            LEFT JOIN categories c
                ON c.id=t.category_id

            LEFT JOIN accounts a
                ON a.id=t.account_id

            WHERE t.user_id=%s

            AND (
                t.description LIKE %s
                OR COALESCE(c.name,'Transfer') LIKE %s
            )
            """


            params = [
                self.user["id"],
                f"%{search.get()}%",
                f"%{search.get()}%"
            ]


            if transaction_type.get() != "ALL":

                query += """
                AND t.transaction_type=%s
                """

                params.append(
                    transaction_type.get()
                )


            query += """
            ORDER BY
                t.transaction_date DESC,
                t.id DESC
            """


            rows = self.db.fetchall(
                query,
                tuple(params)
            )


            for row in rows:

                tree.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["transaction_date"],
                        row["transaction_type"],
                        row["cat"],
                        row["acc"],
                        money(row["amount"]),
                        row["description"]
                    )
                )


        ttk.Button(
            controls,
            text="Search / Refresh",
            command=load
        ).pack(
            side="left",
            padx=8
        )


        # Delete
        def delete():

            selected = tree.selection()

            if not selected:
                return


            transaction_id = tree.item(
                selected[0]
            )["values"][0]


            should_delete = True
            try:
                saved_confirm = self.db.fetchone(
                    """
                    SELECT setting_value
                    FROM app_settings
                    WHERE user_id=%s AND setting_key=%s
                    """,
                    (self.user["id"], "confirm_delete")
                )
                should_delete = not saved_confirm or saved_confirm.get("setting_value", "1") == "1"
            except Exception:
                should_delete = True

            if should_delete and not messagebox.askyesno(
                "Delete",
                "Delete this transaction?"
            ):
                return

            try:
                self.db.execute(
                    """
                    DELETE FROM transactions
                    WHERE id=%s
                    AND user_id=%s
                    """,
                    (
                        transaction_id,
                        self.user["id"]
                    )
                )

                load()

            except Exception as e:
                self.db_error(e)


        ttk.Button(
            controls,
            text="Delete Selected",
            command=delete
        ).pack(
            side="right",
            padx=8
        )


        load()


    # ========================================================
    # ACCOUNTS
    # ========================================================

    def accounts(self):

        body = self.header(
            "Accounts",
            "Manage your bank, cash and wallet accounts"
        )


        left = tk.Frame(
            body,
            bg=WHITE
        )

        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )


        tk.Label(
            left,
            text="Your Accounts",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=18,
            pady=15
        )


        tree = self.make_tree(
            left,
            (
                "ID",
                "Account",
                "Type",
                "Opening",
                "Current Balance"
            ),
            (
                50,
                180,
                130,
                110,
                150
            )
        )


        def load():

            for item in tree.get_children():

                tree.delete(item)


            rows = self.db.fetchall(
                """
                SELECT *
                FROM accounts
                WHERE user_id=%s
                ORDER BY account_name
                """,
                (self.user["id"],)
            )


            for row in rows:

                balance = self.account_balance(
                    row["id"],
                    row["opening_balance"]
                )


                tree.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["account_name"],
                        row["account_type"],
                        money(row["opening_balance"]),
                        money(balance)
                    )
                )


        load()


        # Right panel
        right = tk.Frame(
            body,
            bg=WHITE
        )

        right.pack(
            side="right",
            fill="y",
            padx=(10, 0)
        )


        right.config(
            width=330
        )


        tk.Label(
            right,
            text="Add Account",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=20,
            pady=20
        )


        name = tk.StringVar()

        account_type = tk.StringVar(
            value="Bank Account"
        )

        opening = tk.StringVar(
            value="0"
        )


        self.simple_labeled(
            right,
            "Account Name",
            name
        )


        ttk.Combobox(
            right,
            textvariable=account_type,
            values=[
                "Bank Account",
                "Savings Account",
                "Cash",
                "UPI Wallet",
                "Credit Card",
                "Other"
            ],
            state="readonly"
        ).pack(
            fill="x",
            padx=20,
            pady=6
        )


        tk.Label(
            right,
            text="Account Type",
            bg=WHITE,
            fg=GREY
        ).pack(
            anchor="w",
            padx=20
        )


        self.simple_labeled(
            right,
            f"Opening Balance ({self.currency_symbol})",
            opening
        )


        def add():

            try:

                opening_value = float(
                    opening.get()
                )


                if not name.get().strip():

                    raise ValueError(
                        "Enter account name."
                    )


                self.db.execute(
                    """
                    INSERT INTO accounts
                    (
                        user_id,
                        account_name,
                        account_type,
                        opening_balance
                    )
                    VALUES(%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        name.get().strip(),
                        account_type.get(),
                        opening_value
                    )
                )


                load()

                name.set("")

                opening.set("0")


            except Exception as e:

                self.db_error(e)


        self.yellow_button(
            right,
            "ADD ACCOUNT",
            add
        ).pack(
            fill="x",
            padx=20,
            pady=15,
            ipady=7
        )


        def delete():

            selected = tree.selection()

            if selected:

                account_id = tree.item(
                    selected[0]
                )["values"][0]


                if messagebox.askyesno(
                    "Delete",
                    "Delete this account?\n\n"
                    "Transactions will retain their history."
                ):

                    try:

                        self.db.execute(
                            """
                            DELETE FROM accounts
                            WHERE id=%s
                            AND user_id=%s
                            """,
                            (
                                account_id,
                                self.user["id"]
                            )
                        )


                        load()


                    except Exception as e:

                        self.db_error(e)


        ttk.Button(
            right,
            text="Delete Selected",
            command=delete
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )


    # ========================================================
    # SIMPLE LABELED ENTRY
    # ========================================================

    def simple_labeled(
        self,
        parent,
        label,
        variable
    ):

        tk.Label(
            parent,
            text=label,
            bg=WHITE,
            fg=GREY
        ).pack(
            anchor="w",
            padx=20,
            pady=(7, 0)
        )


        ttk.Entry(
            parent,
            textvariable=variable
        ).pack(
            fill="x",
            padx=20,
            pady=5,
            ipady=5
        )


    # ========================================================
    # ACCOUNT BALANCE
    # ========================================================

    def account_balance(
        self,
        account_id,
        opening
    ):

        row = self.db.fetchone(
            """
            SELECT COALESCE(
                SUM(
                    CASE

                        WHEN transaction_type='INCOME'
                            AND account_id=%s
                            THEN amount

                        WHEN transaction_type='EXPENSE'
                            AND account_id=%s
                            THEN -amount

                        WHEN transaction_type='TRANSFER'
                            AND from_account_id=%s
                            THEN -amount

                        WHEN transaction_type='TRANSFER'
                            AND to_account_id=%s
                            THEN amount

                        ELSE 0

                    END
                ),0
            ) x

            FROM transactions

            WHERE user_id=%s
            """,
            (
                account_id,
                account_id,
                account_id,
                account_id,
                self.user["id"]
            )
        )


        return (
            float(opening)
            +
            float(row["x"] or 0)
        )


    # ========================================================
    # BUDGETS
    # ========================================================

    def budgets(self):

        body = self.header(
            "Monthly Budget",
            "Set your spending limit and category budgets"
        )


        now = date.today()

        month = (
            f"{now.year:04d}-"
            f"{now.month:02d}-01"
        )


        left = tk.Frame(
            body,
            bg=WHITE
        )

        left.pack(
            fill="both",
            expand=True,
            padx=(0, 10)
        )


        tk.Label(
            left,
            text=f"Budget for {now.strftime('%B %Y')}",
            font=("Segoe UI", 16, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=20,
            pady=18
        )


        budget = self.db.fetchone(
            """
            SELECT *
            FROM budgets
            WHERE user_id=%s
            AND budget_month=%s
            """,
            (
                self.user["id"],
                month
            )
        )


        current_expense = float(
            self.db.fetchone(
                """
                SELECT COALESCE(SUM(amount),0) x
                FROM transactions
                WHERE user_id=%s
                AND transaction_type='EXPENSE'
                AND transaction_date>=%s
                """,
                (
                    self.user["id"],
                    month
                )
            )["x"]
        )


        amount = tk.StringVar(
            value=(
                str(round(float(budget["amount"]) * self.currency_rate, 2))
                if budget
                else "0"
            )
        )


        self.simple_labeled(
            left,
            f"Monthly Budget ({self.currency_symbol})",
            amount
        )


        info = tk.Frame(
            left,
            bg="#FFF9D8"
        )

        info.pack(
            fill="x",
            padx=20,
            pady=20
        )


        entered_budget = float(amount.get() or 0)
        remaining = (
            self.amount_to_base(entered_budget)
            -
            current_expense
        )


        tk.Label(
            info,
            text=f"Expenses: {money(current_expense)}",
            bg="#FFF9D8",
            font=("Segoe UI", 11)
        ).pack(
            anchor="w",
            padx=15,
            pady=8
        )


        tk.Label(
            info,
            text=f"Remaining: {money(remaining)}",
            bg="#FFF9D8",
            font=("Segoe UI", 12, "bold"),
            fg=GREEN if remaining >= 0 else RED
        ).pack(
            anchor="w",
            padx=15,
            pady=8
        )


        def save():

            try:

                value = float(
                    amount.get()
                )


                if value < 0:

                    raise ValueError(
                        "Budget cannot be negative."
                    )


                value = self.amount_to_base(value)

                if budget:

                    self.db.execute(
                        """
                        UPDATE budgets
                        SET amount=%s
                        WHERE id=%s
                        AND user_id=%s
                        """,
                        (
                            value,
                            budget["id"],
                            self.user["id"]
                        )
                    )

                else:

                    self.db.execute(
                        """
                        INSERT INTO budgets
                        (
                            user_id,
                            budget_month,
                            amount
                        )
                        VALUES(%s,%s,%s)
                        """,
                        (
                            self.user["id"],
                            month,
                            value
                        )
                    )


                self.check_budget_alert(force=True)

                messagebox.showinfo(
                    "Budget",
                    "Monthly budget saved."
                )


                self.budgets()


            except Exception as e:

                self.db_error(e)


        self.yellow_button(
            left,
            "SAVE MONTHLY BUDGET",
            save
        ).pack(
            anchor="e",
            padx=20,
            pady=10,
            ipadx=15,
            ipady=7
        )


        # Category spending
        right = tk.Frame(
            body,
            bg=WHITE
        )

        right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(10, 0)
        )


        tk.Label(
            right,
            text="Category Spending This Month",
            font=("Segoe UI", 16, "bold"),
            bg=WHITE
        ).pack(
            anchor="w",
            padx=20,
            pady=18
        )


        rows = self.db.fetchall(
            """
            SELECT
                c.name,
                SUM(t.amount) total

            FROM transactions t

            JOIN categories c
                ON c.id=t.category_id

            WHERE t.user_id=%s
            AND t.transaction_type='EXPENSE'
            AND t.transaction_date>=%s

            GROUP BY c.name

            ORDER BY total DESC
            """,
            (
                self.user["id"],
                month
            )
        )


        for row in rows[:10]:

            item = tk.Frame(
                right,
                bg=WHITE
            )

            item.pack(
                fill="x",
                padx=20,
                pady=5
            )


            tk.Label(
                item,
                text=row["name"],
                bg=WHITE,
                font=("Segoe UI", 10)
            ).pack(
                side="left"
            )


            tk.Label(
                item,
                text=money(row["total"]),
                bg=WHITE,
                font=("Segoe UI Semibold", 10)
            ).pack(
                side="right"
            )


    # ========================================================
    # CHARTS
    # ========================================================

    def charts(self):

        body = self.header(
            "Charts & Analytics",
            "Visualize where your money goes"
        )

        controls = tk.Frame(body, bg=WHITE)
        controls.pack(fill="x", pady=(0, 10), ipady=7)

        year = tk.IntVar(value=date.today().year)
        month = tk.IntVar(value=date.today().month)

        tk.Label(controls, text="Year", bg=WHITE).pack(side="left", padx=(15, 5))
        ttk.Spinbox(
            controls, from_=2020, to=2100, textvariable=year, width=8
        ).pack(side="left")

        tk.Label(controls, text="Month", bg=WHITE).pack(side="left", padx=(15, 5))
        ttk.Spinbox(
            controls, from_=1, to=12, textvariable=month, width=5
        ).pack(side="left")

        chart_area = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        chart_area.pack(fill="both", expand=True)

        def draw():
            # Remove the previous chart.
            for widget in chart_area.winfo_children():
                widget.destroy()

            try:
                y = int(year.get())
                m = int(month.get())
                if m < 1 or m > 12:
                    raise ValueError("Month must be between 1 and 12.")

                start = date(y, m, 1)
                if m == 12:
                    end = date(y + 1, 1, 1)
                else:
                    end = date(y, m + 1, 1)

                # Use direct SQL here instead of the external analytics
                # functions. This makes Charts & Analytics independent and
                # ensures the charts use exactly the same transactions that
                # are displayed by the rest of the application.
                category_rows = self.db.fetchall(
                    """
                    SELECT COALESCE(c.name, 'Uncategorized') AS category,
                           COALESCE(SUM(t.amount), 0) AS total
                    FROM transactions t
                    LEFT JOIN categories c ON c.id = t.category_id
                    WHERE t.user_id=%s
                      AND t.transaction_type='EXPENSE'
                      AND t.transaction_date >= %s
                      AND t.transaction_date < %s
                    GROUP BY COALESCE(c.name, 'Uncategorized')
                    ORDER BY total DESC
                    """,
                    (self.user["id"], start, end)
                )

                # Income and expense totals by month for the selected year.
                monthly_rows = self.db.fetchall(
                    """
                    SELECT MONTH(transaction_date) AS month_no,
                           COALESCE(SUM(CASE WHEN transaction_type='INCOME'
                                            THEN amount ELSE 0 END), 0) AS income,
                           COALESCE(SUM(CASE WHEN transaction_type='EXPENSE'
                                            THEN amount ELSE 0 END), 0) AS expense
                    FROM transactions
                    WHERE user_id=%s
                      AND transaction_type IN ('INCOME', 'EXPENSE')
                      AND transaction_date >= %s
                      AND transaction_date < %s
                    GROUP BY MONTH(transaction_date)
                    ORDER BY month_no
                    """,
                    (self.user["id"], date(y, 1, 1), date(y + 1, 1, 1))
                )

                daily_rows = self.db.fetchall(
                    """
                    SELECT DAY(transaction_date) AS day_no,
                           COALESCE(SUM(amount), 0) AS expense
                    FROM transactions
                    WHERE user_id=%s
                      AND transaction_type='EXPENSE'
                      AND transaction_date >= %s
                      AND transaction_date < %s
                    GROUP BY DAY(transaction_date)
                    ORDER BY day_no
                    """,
                    (self.user["id"], start, end)
                )

                fig = plt.Figure(figsize=(10, 6.2), dpi=100)
                ax1 = fig.add_subplot(221)
                ax2 = fig.add_subplot(222)
                ax3 = fig.add_subplot(223)
                ax4 = fig.add_subplot(224)

                # 1. Expense by category
                if category_rows:
                    labels = [str(r["category"]) for r in category_rows]
                    values = [float(r["total"] or 0) * self.currency_rate for r in category_rows]
                    ax1.pie(
                        values,
                        labels=labels,
                        autopct="%1.0f%%",
                        textprops={"fontsize": 7}
                    )
                else:
                    ax1.text(0.5, 0.5, "No expense data", ha="center", va="center")
                ax1.set_title("Expense by Category")

                # 2. Income vs expense by month
                month_names = [calendar.month_abbr[i] for i in range(1, 13)]
                income_values = [0.0] * 12
                expense_values = [0.0] * 12
                for r in monthly_rows:
                    idx = int(r["month_no"]) - 1
                    if 0 <= idx < 12:
                        income_values[idx] = float(r["income"] or 0) * self.currency_rate
                        expense_values[idx] = float(r["expense"] or 0) * self.currency_rate

                if any(income_values) or any(expense_values):
                    ax2.plot(month_names, income_values, marker="o", label="Income")
                    ax2.plot(month_names, expense_values, marker="o", label="Expense")
                    ax2.legend(fontsize=7)
                else:
                    ax2.text(0.5, 0.5, "No income/expense data", ha="center", va="center")
                ax2.set_title(f"Income vs Expense - {y}")
                ax2.tick_params(axis="x", rotation=45, labelsize=7)

                # 3. Daily expense for selected month
                if daily_rows:
                    days = [str(int(r["day_no"])) for r in daily_rows]
                    daily_values = [float(r["expense"] or 0) * self.currency_rate for r in daily_rows]
                    ax3.bar(days, daily_values)
                else:
                    ax3.text(0.5, 0.5, "No expense data", ha="center", va="center")
                ax3.set_title(f"Daily Expense - {start.strftime('%b %Y')}")
                ax3.set_xlabel("Day", fontsize=8)
                ax3.tick_params(axis="x", rotation=60, labelsize=7)

                # 4. Top 5 expense categories
                top_rows = category_rows[:5]
                if top_rows:
                    top_labels = [str(r["category"]) for r in top_rows][::-1]
                    top_values = [float(r["total"] or 0) * self.currency_rate for r in top_rows][::-1]
                    ax4.barh(top_labels, top_values)
                else:
                    ax4.text(0.5, 0.5, "No expense data", ha="center", va="center")
                ax4.set_title("Top 5 Categories")

                fig.tight_layout(pad=2.0)

                # Keep strong references to both objects. Do not use a local
                # FigureCanvasTkAgg only, because it can disappear after draw.
                self.chart_figure = fig
                self.chart_canvas = FigureCanvasTkAgg(fig, master=chart_area)
                self.chart_canvas.draw()
                chart_widget = self.chart_canvas.get_tk_widget()
                chart_widget.pack(fill="both", expand=True, padx=8, pady=8)
                chart_area.update_idletasks()
                self.chart_canvas.draw()

            except Exception as e:
                # Never leave a blank screen if the database or chart code
                # fails. Show the actual error inside the Charts page.
                error_frame = tk.Frame(chart_area, bg=WHITE)
                error_frame.pack(fill="both", expand=True)
                tk.Label(
                    error_frame,
                    text="Unable to generate charts",
                    font=("Segoe UI", 16, "bold"),
                    bg=WHITE,
                    fg=RED
                ).pack(pady=(100, 8))
                tk.Label(
                    error_frame,
                    text=str(e),
                    font=("Segoe UI", 10),
                    bg=WHITE,
                    fg=GREY,
                    wraplength=700,
                    justify="center"
                ).pack(padx=30)

        self.yellow_button(
            controls,
            "GENERATE CHARTS",
            draw
        ).pack(side="left", padx=15)

        draw()


    # ========================================================
    # REPORTS
    # ========================================================

    def reports(self):

        body = self.header(
            "Reports",
            "Export your financial records"
        )


        form = tk.Frame(
            body,
            bg=WHITE
        )

        form.pack(
            fill="x",
            ipady=18
        )


        start = tk.StringVar(
            value=(
                f"{date.today().year}-"
                f"{date.today().month:02d}-01"
            )
        )


        end = tk.StringVar(
            value=str(date.today())
        )


        self.field(
            form,
            "From Date",
            start,
            0,
            0
        )


        self.field(
            form,
            "To Date",
            end,
            0,
            1
        )


        form.grid_columnconfigure(
            0,
            weight=1
        )

        form.grid_columnconfigure(
            1,
            weight=1
        )


        output = tk.Label(
            body,
            text=(
                "Choose an export format. "
                "Reports are saved in generated_reports."
            ),
            bg=BG,
            fg=GREY,
            font=("Segoe UI", 10)
        )

        output.pack(
            anchor="w",
            pady=10
        )


        buttons = tk.Frame(
            body,
            bg=BG
        )

        buttons.pack(
            anchor="w"
        )


        def make_report(kind):

            try:

                dataframe = transaction_dataframe(
                    self.db,
                    self.user["id"],
                    start.get(),
                    end.get()
                )


                if kind == "CSV":

                    path = export_csv(
                        dataframe
                    )

                elif kind == "Excel":

                    path = export_excel(
                        dataframe
                    )

                else:

                    path = export_pdf(
                        dataframe
                    )


                output.config(
                    text=f"Saved: {path}",
                    fg=GREEN
                )


                messagebox.showinfo(
                    "Report Created",
                    str(path)
                )


            except Exception as e:

                self.db_error(e)


        for kind in [
            "CSV",
            "Excel",
            "PDF"
        ]:

            self.yellow_button(
                buttons,
                f"EXPORT {kind}",
                lambda x=kind: make_report(x)
            ).pack(
                side="left",
                padx=(0, 10),
                ipadx=15,
                ipady=7
            )


    # ========================================================
    # NEW FEATURE TABLES
    # ========================================================

    def ensure_feature_tables(self):

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                goal_name VARCHAR(150) NOT NULL,
                target_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                current_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                target_date DATE NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(150) NOT NULL,
                description VARCHAR(500) NULL,
                amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                reminder_date DATE NOT NULL,
                repeat_type VARCHAR(20) NOT NULL DEFAULT 'ONCE',
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                setting_key VARCHAR(80) NOT NULL,
                setting_value VARCHAR(255) NOT NULL,
                UNIQUE KEY unique_user_setting (user_id, setting_key)
            )
            """
        )


    # ========================================================
    # FINANCIAL GOALS
    # ========================================================

    def financial_goals(self):

        body = self.header(
            "Financial Goals",
            "Set savings targets and track your progress"
        )

        top = tk.Frame(body, bg=WHITE)
        top.pack(fill="x", pady=(0, 12), ipadx=15, ipady=15)

        tk.Label(
            top,
            text="Create a Financial Goal",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=(5, 15))

        form = tk.Frame(top, bg=WHITE)
        form.pack(fill="x", padx=12)

        name = tk.StringVar()
        target = tk.StringVar()
        current = tk.StringVar(value="0")
        target_date = tk.StringVar()

        self.field(form, "Goal Name", name, 0, 0)
        self.field(form, f"Target Amount ({self.currency_symbol})", target, 0, 1)
        self.field(form, f"Current Saved ({self.currency_symbol})", current, 1, 0)
        self.field(form, "Target Date (YYYY-MM-DD)", target_date, 1, 1)

        for column in (0, 1):
            form.grid_columnconfigure(column, weight=1)

        def add_goal():

            try:
                goal_name = name.get().strip()
                target_amount = float(target.get())
                current_amount = float(current.get() or 0)

                if not goal_name:
                    raise ValueError("Enter a goal name.")

                if target_amount <= 0:
                    raise ValueError("Target amount must be greater than zero.")

                if current_amount < 0:
                    raise ValueError("Current saved amount cannot be negative.")

                if current_amount > target_amount:
                    raise ValueError("Current saved amount cannot exceed the target.")

                goal_date = target_date.get().strip() or None

                # Store goal amounts in INR.
                target_amount = self.amount_to_base(target_amount)
                current_amount = self.amount_to_base(current_amount)

                if goal_date:
                    datetime.strptime(goal_date, "%Y-%m-%d")

                self.db.execute(
                    """
                    INSERT INTO financial_goals
                    (user_id, goal_name, target_amount, current_amount,
                     target_date, status)
                    VALUES(%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        goal_name,
                        target_amount,
                        current_amount,
                        goal_date,
                        "COMPLETED" if current_amount >= target_amount else "ACTIVE"
                    )
                )

                messagebox.showinfo("Goal", "Financial goal created successfully.")
                self.financial_goals()

            except ValueError as e:
                messagebox.showwarning("Invalid Data", str(e))
            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            top,
            "ADD GOAL",
            add_goal
        ).pack(anchor="e", padx=20, pady=(12, 5), ipadx=15, ipady=7)

        panel = tk.Frame(body, bg=WHITE)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="Your Goals",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=15)

        rows = self.db.fetchall(
            """
            SELECT *
            FROM financial_goals
            WHERE user_id=%s
            ORDER BY
                CASE WHEN status='ACTIVE' THEN 0 ELSE 1 END,
                id DESC
            """,
            (self.user["id"],)
        )

        if not rows:
            tk.Label(
                panel,
                text="No financial goals yet. Create your first savings goal above.",
                bg=WHITE,
                fg=GREY,
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=20, pady=10)
            return

        for row in rows:

            target_amount = float(row["target_amount"] or 0)
            current_amount = float(row["current_amount"] or 0)
            percentage = min(
                100,
                (current_amount / target_amount * 100)
                if target_amount else 0
            )

            card = tk.Frame(
                panel,
                bg="#FFF9D8",
                highlightbackground="#E6E6E6",
                highlightthickness=1
            )
            card.pack(fill="x", padx=20, pady=6)

            heading = tk.Frame(card, bg="#FFF9D8")
            heading.pack(fill="x", padx=15, pady=(10, 3))

            tk.Label(
                heading,
                text=row["goal_name"],
                font=("Segoe UI Semibold", 12),
                bg="#FFF9D8",
                fg=DARK
            ).pack(side="left")

            tk.Label(
                heading,
                text=f"{percentage:.0f}%",
                font=("Segoe UI Semibold", 11),
                bg="#FFF9D8",
                fg=GREEN if percentage >= 100 else DARK
            ).pack(side="right")

            tk.Label(
                card,
                text=f"{money(current_amount)} saved of {money(target_amount)}",
                bg="#FFF9D8",
                fg=GREY,
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=15)

            progress = ttk.Progressbar(
                card,
                maximum=100,
                value=percentage
            )
            progress.pack(fill="x", padx=15, pady=8)

            if row["target_date"]:
                tk.Label(
                    card,
                    text=f"Target date: {row['target_date']}",
                    bg="#FFF9D8",
                    fg=GREY,
                    font=("Segoe UI", 9)
                ).pack(anchor="w", padx=15, pady=(0, 8))

            buttons = tk.Frame(card, bg="#FFF9D8")
            buttons.pack(anchor="e", padx=15, pady=(0, 10))

            def update_goal(goal_id=row["id"],
                            old_current=current_amount,
                            goal_target=target_amount):

                value = simpledialog.askstring(
                    "Update Goal",
                    f"Enter total amount currently saved ({self.currency_symbol}):",
                    initialvalue=str(old_current)
                )

                if value is None:
                    return

                try:
                    new_amount = float(value)

                    if new_amount < 0 or new_amount > goal_target:
                        raise ValueError

                    status = "COMPLETED" if new_amount >= goal_target else "ACTIVE"

                    self.db.execute(
                        """
                        UPDATE financial_goals
                        SET current_amount=%s, status=%s
                        WHERE id=%s AND user_id=%s
                        """,
                        (new_amount, status, goal_id, self.user["id"])
                    )

                    self.financial_goals()

                except ValueError:
                    messagebox.showwarning(
                        "Invalid Amount",
                        "Enter an amount between 0 and the target."
                    )
                except Exception as e:
                    self.db_error(e)

            def delete_goal(goal_id=row["id"]):

                if messagebox.askyesno(
                    "Delete Goal",
                    "Delete this financial goal?"
                ):
                    try:
                        self.db.execute(
                            """
                            DELETE FROM financial_goals
                            WHERE id=%s AND user_id=%s
                            """,
                            (goal_id, self.user["id"])
                        )
                        self.financial_goals()
                    except Exception as e:
                        self.db_error(e)

            ttk.Button(
                buttons,
                text="Update Saved",
                command=update_goal
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons,
                text="Delete",
                command=delete_goal
            ).pack(side="left", padx=5)


    # ========================================================
    # RECURRING TRANSACTIONS
    # ========================================================

    # ========================================================
    # FINANCIAL ALERTS
    # ========================================================

    def _setting_enabled(self, key, default=True):
        try:
            row = self.db.fetchone(
                """
                SELECT setting_value
                FROM app_settings
                WHERE user_id=%s AND setting_key=%s
                """,
                (self.user["id"], key)
            )
            if not row:
                return default
            return str(row.get("setting_value", "1")) == "1"
        except Exception:
            return default


    def check_budget_alert(self, force=False):
        """Show a warning when the current month's expenses exceed its budget."""
        if not self.user or not self._setting_enabled("budget_alerts", True):
            return

        today = date.today()
        month_start = today.replace(day=1)

        try:
            budget_row = self.db.fetchone(
                """
                SELECT amount
                FROM budgets
                WHERE user_id=%s AND budget_month=%s
                """,
                (self.user["id"], month_start.strftime("%Y-%m-%d"))
            )

            if not budget_row:
                return

            budget_amount = float(budget_row["amount"] or 0)
            if budget_amount <= 0:
                return

            expense_row = self.db.fetchone(
                """
                SELECT COALESCE(SUM(amount),0) AS total
                FROM transactions
                WHERE user_id=%s
                  AND transaction_type='EXPENSE'
                  AND transaction_date >= %s
                  AND transaction_date < %s
                """,
                (
                    self.user["id"],
                    month_start.strftime("%Y-%m-%d"),
                    (date(today.year + (1 if today.month == 12 else 0),
                          1 if today.month == 12 else today.month + 1,
                          1)).strftime("%Y-%m-%d")
                )
            )
            expenses = float(expense_row["total"] or 0)

            if expenses <= budget_amount:
                return

            alert_key = f"budget:{today.strftime('%Y-%m')}"
            if not force and alert_key in self._shown_alerts:
                return

            self._shown_alerts.add(alert_key)
            exceeded = expenses - budget_amount

            messagebox.showwarning(
                "Budget Alert",
                "Your monthly budget has been exceeded!\n\n"
                f"Budget: {money(budget_amount)}\n"
                f"Expenses: {money(expenses)}\n"
                f"Exceeded by: {money(exceeded)}"
            )

        except Exception as e:
            self.db_error(e)


    def check_reminder_alerts(self):
        """Show pending reminders that are due today or overdue."""
        if not self.user or not self._setting_enabled("reminder_notifications", True):
            return

        today = date.today()

        try:
            rows = self.db.fetchall(
                """
                SELECT id, title, amount, reminder_date, repeat_type, status
                FROM reminders
                WHERE user_id=%s
                  AND status='PENDING'
                  AND reminder_date <= %s
                ORDER BY reminder_date ASC, id ASC
                """,
                (self.user["id"], today.strftime("%Y-%m-%d"))
            )

            pending_alerts = []
            for row in rows:
                alert_key = f"reminder:{row['id']}:{row['reminder_date']}"
                if alert_key in self._shown_alerts:
                    continue

                due = row["reminder_date"]
                if isinstance(due, str):
                    due = datetime.strptime(due, "%Y-%m-%d").date()

                state = "OVERDUE" if due < today else "DUE TODAY"
                pending_alerts.append((row, state, alert_key))

            if not pending_alerts:
                return

            # Avoid an alert storm when several reminders are due at once.
            for _, _, alert_key in pending_alerts[:5]:
                self._shown_alerts.add(alert_key)

            lines = ["You have financial reminders that need your attention:\n"]
            for row, state, _ in pending_alerts[:5]:
                amount_text = money(row["amount"]) if float(row["amount"] or 0) > 0 else "No amount"
                lines.append(
                    f"• {row['title']} — {state} ({row['reminder_date']}) — {amount_text}"
                )

            if len(pending_alerts) > 5:
                lines.append(f"\n+ {len(pending_alerts) - 5} more reminder(s)")

            messagebox.showwarning(
                "Reminder Notification",
                "\n".join(lines)
            )

        except Exception as e:
            self.db_error(e)


    def check_financial_alerts(self):
        """Run enabled reminder and budget alerts after login and periodically."""
        if not self.user:
            self._alert_job = None
            return

        self.check_reminder_alerts()
        self.check_budget_alert()

        # Keep checking while the user is logged in so a reminder that becomes
        # due or a budget that is exceeded during the session can trigger an alert.
        self._alert_job = self.after(60000, self.check_financial_alerts)


    def reminders(self):

        body = self.header(
            "Reminders",
            "Keep track of upcoming bills, payments and important financial dates"
        )

        top = tk.Frame(body, bg=WHITE)
        top.pack(fill="x", pady=(0, 12), ipadx=15, ipady=15)

        tk.Label(
            top,
            text="Create Reminder",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=(5, 15))

        form = tk.Frame(top, bg=WHITE)
        form.pack(fill="x", padx=12)

        title = tk.StringVar()
        description = tk.StringVar()
        amount = tk.StringVar(value="0")
        reminder_date = tk.StringVar(value=str(date.today()))
        repeat_type = tk.StringVar(value="ONCE")

        self.field(form, "Reminder Title", title, 0, 0)
        self.field(form, f"Amount ({self.currency_symbol})", amount, 0, 1)
        self.field(form, "Due Date (YYYY-MM-DD)", reminder_date, 0, 2)

        self.field(form, "Description", description, 1, 0)

        repeat_box = tk.Frame(form, bg=WHITE)
        repeat_box.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=8,
            pady=5
        )

        tk.Label(
            repeat_box,
            text="Repeat",
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w")

        ttk.Combobox(
            repeat_box,
            textvariable=repeat_type,
            values=["ONCE", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"],
            state="readonly"
        ).pack(fill="x", ipady=5, pady=(3, 0))

        for column in range(3):
            form.grid_columnconfigure(column, weight=1)

        def add_reminder():

            try:
                reminder_title = title.get().strip()
                reminder_amount = float(amount.get() or 0)
                reminder_day = reminder_date.get().strip()

                if not reminder_title:
                    raise ValueError("Enter a reminder title.")

                if reminder_amount < 0:
                    raise ValueError("Amount cannot be negative.")

                datetime.strptime(
                    reminder_day,
                    "%Y-%m-%d"
                )

                reminder_amount = self.amount_to_base(reminder_amount)

                self.db.execute(
                    """
                    INSERT INTO reminders
                    (
                        user_id,
                        title,
                        description,
                        amount,
                        reminder_date,
                        repeat_type,
                        status
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        reminder_title,
                        description.get(),
                        reminder_amount,
                        reminder_day,
                        repeat_type.get(),
                        "PENDING"
                    )
                )

                messagebox.showinfo(
                    "Reminder",
                    "Reminder created successfully."
                )

                self.reminders()

            except ValueError as e:
                messagebox.showwarning(
                    "Invalid Data",
                    str(e)
                )
            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            top,
            "ADD REMINDER",
            add_reminder
        ).pack(
            anchor="e",
            padx=20,
            pady=(12, 5),
            ipadx=15,
            ipady=7
        )

        panel = tk.Frame(body, bg=WHITE)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="Upcoming & Overdue Reminders",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=15)

        rows = self.db.fetchall(
            """
            SELECT *
            FROM reminders
            WHERE user_id=%s
            ORDER BY
                CASE WHEN status='PENDING' THEN 0 ELSE 1 END,
                reminder_date ASC,
                id DESC
            """,
            (self.user["id"],)
        )

        if not rows:
            tk.Label(
                panel,
                text="No reminders yet. Add your first financial reminder above.",
                bg=WHITE,
                fg=GREY,
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=20, pady=10)
            return

        tree = self.make_tree(
            panel,
            (
                "ID",
                "Title",
                "Amount",
                "Due Date",
                "Repeat",
                "Status",
                "Description"
            ),
            (
                55,
                220,
                120,
                120,
                100,
                100,
                260
            )
        )

        today = date.today()

        for row in rows:

            due = row["reminder_date"]

            if isinstance(due, str):
                due = datetime.strptime(
                    due,
                    "%Y-%m-%d"
                ).date()

            display_status = row["status"]

            if row["status"] == "PENDING" and due < today:
                display_status = "OVERDUE"

            tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["title"],
                    money(row["amount"]),
                    row["reminder_date"],
                    row["repeat_type"],
                    display_status,
                    row["description"] or ""
                )
            )

        buttons = tk.Frame(panel, bg=WHITE)
        buttons.pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        def complete_selected():

            selection = tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Reminder",
                    "Select a reminder first."
                )
                return

            row = rows[tree.index(selection[0])]

            try:
                if row["repeat_type"] == "ONCE":

                    self.db.execute(
                        """
                        UPDATE reminders
                        SET status='COMPLETED'
                        WHERE id=%s AND user_id=%s
                        """,
                        (row["id"], self.user["id"])
                    )

                else:

                    new_date = self.next_recurring_date(
                        row["reminder_date"],
                        row["repeat_type"]
                    )

                    self.db.execute(
                        """
                        UPDATE reminders
                        SET reminder_date=%s, status='PENDING'
                        WHERE id=%s AND user_id=%s
                        """,
                        (
                            new_date,
                            row["id"],
                            self.user["id"]
                        )
                    )

                self.reminders()

            except Exception as e:
                self.db_error(e)

        def delete_selected():

            selection = tree.selection()

            if not selection:
                return

            row = rows[tree.index(selection[0])]

            if messagebox.askyesno(
                "Delete Reminder",
                "Delete this reminder?"
            ):

                try:
                    self.db.execute(
                        """
                        DELETE FROM reminders
                        WHERE id=%s AND user_id=%s
                        """,
                        (
                            row["id"],
                            self.user["id"]
                        )
                    )

                    self.reminders()

                except Exception as e:
                    self.db_error(e)

        ttk.Button(
            buttons,
            text="Mark Completed",
            command=complete_selected
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ttk.Button(
            buttons,
            text="Delete Selected",
            command=delete_selected
        ).pack(
            side="left",
            padx=8
        )


    # ========================================================
    # CATEGORIES
    # ========================================================

    def categories(self):

        body = self.header(
            "Categories",
            "Manage your expense and income categories"
        )

        top = tk.Frame(body, bg=WHITE)
        top.pack(fill="x", pady=(0, 12), ipadx=15, ipady=15)

        tk.Label(
            top,
            text="Add Custom Category",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=(5, 15))

        form = tk.Frame(top, bg=WHITE)
        form.pack(fill="x", padx=12)

        name = tk.StringVar()
        category_type = tk.StringVar(value="EXPENSE")
        icon = tk.StringVar(value="●")

        self.field(form, "Category Name", name, 0, 0)

        type_box = tk.Frame(form, bg=WHITE)
        type_box.grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        tk.Label(type_box, text="Category Type", bg=WHITE, fg=GREY).pack(anchor="w")
        ttk.Combobox(
            type_box,
            textvariable=category_type,
            values=["EXPENSE", "INCOME"],
            state="readonly"
        ).pack(fill="x", ipady=5, pady=(3, 0))

        self.field(form, "Icon", icon, 0, 2)

        for column in range(3):
            form.grid_columnconfigure(column, weight=1)

        def add_category():

            category_name = name.get().strip()

            if not category_name:
                messagebox.showwarning(
                    "Category",
                    "Enter a category name."
                )
                return

            try:
                existing = self.db.fetchone(
                    """
                    SELECT id
                    FROM categories
                    WHERE user_id=%s AND name=%s AND category_type=%s
                    """,
                    (
                        self.user["id"],
                        category_name,
                        category_type.get()
                    )
                )

                if existing:
                    messagebox.showwarning(
                        "Category",
                        "This category already exists."
                    )
                    return

                self.db.execute(
                    """
                    INSERT INTO categories
                    (user_id, name, category_type, icon, color)
                    VALUES(%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        category_name,
                        category_type.get(),
                        icon.get().strip() or "●",
                        YELLOW
                    )
                )

                messagebox.showinfo(
                    "Category",
                    "Category added successfully."
                )
                self.categories()

            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            top,
            "ADD CATEGORY",
            add_category
        ).pack(anchor="e", padx=20, pady=(12, 5), ipadx=15, ipady=7)

        panel = tk.Frame(body, bg=WHITE)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="Your Categories",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=20, pady=15)

        rows = self.db.fetchall(
            """
            SELECT id, name, category_type, icon
            FROM categories
            WHERE user_id=%s
            ORDER BY category_type, name
            """,
            (self.user["id"],)
        )

        tree = self.make_tree(
            panel,
            ("ID", "Icon", "Category", "Type"),
            (60, 80, 250, 120)
        )

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["icon"],
                    row["name"],
                    row["category_type"]
                )
            )

        def delete_category():

            selection = tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Category",
                    "Select a category first."
                )
                return

            category_id = tree.item(selection[0])["values"][0]

            if not messagebox.askyesno(
                "Delete Category",
                "Delete the selected category?"
            ):
                return

            try:
                self.db.execute(
                    """
                    DELETE FROM categories
                    WHERE id=%s AND user_id=%s
                    """,
                    (category_id, self.user["id"])
                )
                self.categories()

            except Exception as e:
                messagebox.showerror(
                    "Category",
                    "This category may already be used by a transaction.\n\n"
                    "Used categories cannot be deleted."
                )

        ttk.Button(
            panel,
            text="Delete Selected",
            command=delete_category
        ).pack(anchor="w", padx=20, pady=(0, 15))


    # ========================================================
    # PROFILE
    # ========================================================

    def settings(self):

        body = self.header(
            "Settings",
            "Customize your expense tracker and manage your account"
        )

        # Scrollable settings content
        scroll_container = tk.Frame(body, bg=BG)
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            scroll_container,
            bg=BG,
            highlightthickness=0,
            borderwidth=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        content = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window(
            (0, 0),
            window=content,
            anchor="nw"
        )

        def update_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_content(event):
            canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", update_scroll)
        canvas.bind("<Configure>", resize_content)

        def wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind(
            "<Enter>",
            lambda event: canvas.bind_all("<MouseWheel>", wheel)
        )
        canvas.bind(
            "<Leave>",
            lambda event: canvas.unbind_all("<MouseWheel>")
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load saved settings
        def get_setting(key, default):
            try:
                row = self.db.fetchone(
                    """
                    SELECT setting_value
                    FROM app_settings
                    WHERE user_id=%s AND setting_key=%s
                    """,
                    (self.user["id"], key)
                )
                return row["setting_value"] if row else default
            except Exception:
                return default

        currency = tk.StringVar(
            value=get_setting("currency", "Indian Rupee (₹)")
        )
        default_payment_method = tk.StringVar(
            value=get_setting("default_payment_method", "UPI")
        )
        confirm_delete = tk.BooleanVar(
            value=get_setting("confirm_delete", "1") == "1"
        )
        reminder_notifications = tk.BooleanVar(
            value=get_setting("reminder_notifications", "1") == "1"
        )
        budget_alerts = tk.BooleanVar(
            value=get_setting("budget_alerts", "1") == "1"
        )

        def section(title, subtitle):
            frame = tk.Frame(
                content,
                bg=WHITE,
                highlightbackground="#E6E6E6",
                highlightthickness=1
            )
            frame.pack(fill="x", pady=(0, 14))

            tk.Label(
                frame,
                text=title,
                font=("Segoe UI", 15, "bold"),
                bg=WHITE,
                fg=DARK
            ).pack(anchor="w", padx=25, pady=(18, 2))

            tk.Label(
                frame,
                text=subtitle,
                font=("Segoe UI", 9),
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w", padx=25, pady=(0, 12))

            return frame

        # --------------------------------------------------------
        # General
        # --------------------------------------------------------

        general = section(
            "General",
            "Basic preferences for your financial records"
        )

        general_form = tk.Frame(general, bg=WHITE)
        general_form.pack(fill="x", padx=17, pady=(0, 5))

        def setting_combo(parent, label, variable, values, row, column):
            box = tk.Frame(parent, bg=WHITE)
            box.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=8,
                pady=6
            )

            tk.Label(
                box,
                text=label,
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Combobox(
                box,
                textvariable=variable,
                values=values,
                state="readonly"
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 0)
            )

        setting_combo(
            general_form,
            "Currency",
            currency,
            ["Indian Rupee (₹)", "US Dollar ($)", "Euro (€)", "British Pound (£)"],
            0,
            0
        )

        setting_combo(
            general_form,
            "Default Payment Method",
            default_payment_method,
            ["UPI", "Cash", "Debit Card", "Credit Card", "Bank Transfer", "Other"],
            0,
            1
        )

        confirm_row = tk.Frame(general, bg=WHITE)
        confirm_row.pack(fill="x", padx=25, pady=(2, 16))
        confirm_text = tk.Frame(confirm_row, bg=WHITE)
        confirm_text.pack(side="left", fill="x", expand=True)
        tk.Label(
            confirm_text,
            text="Confirm Before Delete",
            font=("Segoe UI Semibold", 10),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w")
        tk.Label(
            confirm_text,
            text="Ask for confirmation before deleting a transaction.",
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w", pady=(2, 0))
        ttk.Checkbutton(
            confirm_row,
            text="ON",
            variable=confirm_delete
        ).pack(side="right", padx=(10, 0))

        general_form.grid_columnconfigure(0, weight=1)
        general_form.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------
        # Notifications
        # --------------------------------------------------------

        notifications = section(
            "Notifications",
            "Choose which financial alerts you want to receive"
        )

        def setting_switch(parent, text, variable, description):
            row = tk.Frame(parent, bg=WHITE)
            row.pack(fill="x", padx=25, pady=7)

            text_area = tk.Frame(row, bg=WHITE)
            text_area.pack(side="left", fill="x", expand=True)

            tk.Label(
                text_area,
                text=text,
                font=("Segoe UI Semibold", 10),
                bg=WHITE,
                fg=DARK
            ).pack(anchor="w")

            tk.Label(
                text_area,
                text=description,
                font=("Segoe UI", 9),
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w", pady=(2, 0))

            ttk.Checkbutton(
                row,
                text="ON",
                variable=variable
            ).pack(side="right", padx=(10, 0))

        setting_switch(
            notifications,
            "Reminder Notifications",
            reminder_notifications,
            "Show reminders for upcoming bills and financial dates."
        )

        setting_switch(
            notifications,
            "Budget Alerts",
            budget_alerts,
            "Show alerts when your monthly spending approaches the budget."
        )

        # --------------------------------------------------------
        # Security
        # --------------------------------------------------------

        security = section(
            "Security",
            "Manage your account security"
        )

        security_row = tk.Frame(security, bg=WHITE)
        security_row.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        tk.Label(
            security_row,
            text="Password and account security",
            font=("Segoe UI Semibold", 10),
            bg=WHITE,
            fg=DARK
        ).pack(side="left")

        ttk.Button(
            security_row,
            text="CHANGE PASSWORD",
            command=self.profile
        ).pack(side="right")

        # --------------------------------------------------------
        # Data & Privacy
        # --------------------------------------------------------

        data = section(
            "Data & Privacy",
            "Export your records or review your account information"
        )

        data_buttons = tk.Frame(data, bg=WHITE)
        data_buttons.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        def export_all_data():
            try:
                df = transaction_dataframe(
                    self.db,
                    self.user["id"],
                    "2000-01-01",
                    str(date.today())
                )
                if "amount" in df.columns:
                    df["amount"] = df["amount"] * self.currency_rate
                output = export_excel(df)
                messagebox.showinfo(
                    "Export Complete",
                    f"Your financial data was exported successfully.\n\n{output}"
                )
            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            data_buttons,
            "EXPORT ALL DATA",
            export_all_data
        ).pack(
            side="left",
            ipadx=15,
            ipady=7
        )

        ttk.Button(
            data_buttons,
            text="VIEW PROFILE",
            command=self.profile
        ).pack(
            side="left",
            padx=10,
            ipadx=10,
            ipady=5
        )

        # --------------------------------------------------------
        # About
        # --------------------------------------------------------

        about = section(
            "About",
            "Smart Personal Expense Tracker"
        )

        tk.Label(
            about,
            text=(
                "Version 1.0\n\n"
                "A personal finance management application for tracking "
                "income, expenses, accounts, budgets, reminders and "
                "financial goals.\n\n"
                "Built with Python, Tkinter and MySQL."
            ),
            font=("Segoe UI", 10),
            bg=WHITE,
            fg=GREY,
            justify="left"
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 18)
        )

        # --------------------------------------------------------
        # Save / Reset
        # --------------------------------------------------------

        actions = tk.Frame(content, bg=BG)
        actions.pack(fill="x", pady=(0, 20))

        def save_settings():
            values = {
                "currency": currency.get(),
                "default_payment_method": default_payment_method.get(),
                "confirm_delete": "1" if confirm_delete.get() else "0",
                "reminder_notifications": "1" if reminder_notifications.get() else "0",
                "budget_alerts": "1" if budget_alerts.get() else "0"
            }

            try:
                for key, value in values.items():
                    self.db.execute(
                        """
                        INSERT INTO app_settings
                        (user_id, setting_key, setting_value)
                        VALUES(%s,%s,%s)
                        ON DUPLICATE KEY UPDATE
                        setting_value=VALUES(setting_value)
                        """,
                        (
                            self.user["id"],
                            key,
                            value
                        )
                    )

                self.apply_currency_setting(currency.get())

                messagebox.showinfo(
                    "Settings",
                    "Settings saved successfully. Currency changes are now applied across the app."
                )

                self.dashboard()

            except Exception as e:
                self.db_error(e)

        def reset_settings():
            currency.set("Indian Rupee (₹)")
            default_payment_method.set("UPI")
            confirm_delete.set(True)
            reminder_notifications.set(True)
            budget_alerts.set(True)

        self.yellow_button(
            actions,
            "SAVE SETTINGS",
            save_settings
        ).pack(
            side="right",
            ipadx=18,
            ipady=8
        )

        ttk.Button(
            actions,
            text="RESET TO DEFAULT",
            command=reset_settings
        ).pack(
            side="right",
            padx=10,
            ipadx=10,
            ipady=6
        )

    def profile(self):

        body = self.header(
            "Profile",
            "Manage your personal information and account security"
        )

        # --------------------------------------------------------
        # Scrollable Profile content
        # --------------------------------------------------------

        scroll_container = tk.Frame(
            body,
            bg=BG
        )
        scroll_container.pack(
            fill="both",
            expand=True
        )

        profile_canvas = tk.Canvas(
            scroll_container,
            bg=BG,
            highlightthickness=0,
            borderwidth=0
        )
        profile_scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=profile_canvas.yview
        )

        profile_canvas.configure(
            yscrollcommand=profile_scrollbar.set
        )

        profile_scrollbar.pack(
            side="right",
            fill="y"
        )
        profile_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        profile_content = tk.Frame(
            profile_canvas,
            bg=BG
        )

        profile_window = profile_canvas.create_window(
            (0, 0),
            window=profile_content,
            anchor="nw"
        )

        def update_scroll_region(event=None):
            profile_canvas.configure(
                scrollregion=profile_canvas.bbox("all")
            )

        def resize_profile_content(event):
            profile_canvas.itemconfigure(
                profile_window,
                width=event.width
            )

        profile_content.bind(
            "<Configure>",
            update_scroll_region
        )
        profile_canvas.bind(
            "<Configure>",
            resize_profile_content
        )

        def mousewheel(event):
            profile_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        profile_canvas.bind(
            "<Enter>",
            lambda event: profile_canvas.bind_all(
                "<MouseWheel>",
                mousewheel
            )
        )
        profile_canvas.bind(
            "<Leave>",
            lambda event: profile_canvas.unbind_all(
                "<MouseWheel>"
            )
        )

        # All Profile cards are placed inside this scrollable frame.
        body = profile_content

        # --------------------------------------------------------
        # Profile header
        # --------------------------------------------------------

        profile_header = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        profile_header.pack(fill="x", pady=(0, 15))

        avatar = tk.Label(
            profile_header,
            text=self.user["name"][:1].upper(),
            font=("Segoe UI", 22, "bold"),
            bg=YELLOW,
            fg=DARK,
            width=3,
            height=2
        )
        avatar.pack(side="left", padx=25, pady=20)

        details = tk.Frame(profile_header, bg=WHITE)
        details.pack(side="left", fill="x", expand=True, pady=20)

        tk.Label(
            details,
            text=self.user["name"],
            font=("Segoe UI", 20, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w")

        tk.Label(
            details,
            text=self.user["email"],
            font=("Segoe UI", 10),
            bg=WHITE,
            fg=GREY
        ).pack(anchor="w", pady=(3, 0))

        # --------------------------------------------------------
        # Personal information
        # --------------------------------------------------------

        info = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        info.pack(fill="x", pady=(0, 15))

        tk.Label(
            info,
            text="Personal Information",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=25, pady=(18, 10))

        form = tk.Frame(info, bg=WHITE)
        form.pack(fill="x", padx=17)

        name = tk.StringVar(value=self.user["name"])
        email = tk.StringVar(value=self.user["email"])

        self.field(form, "Full Name", name, 0, 0)
        self.field(form, "Email", email, 0, 1)

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        def save_profile():

            new_name = name.get().strip()
            new_email = email.get().strip().lower()

            if not new_name:
                messagebox.showwarning(
                    "Profile",
                    "Name cannot be empty."
                )
                return

            if "@" not in new_email:
                messagebox.showwarning(
                    "Profile",
                    "Enter a valid email address."
                )
                return

            try:

                existing = self.db.fetchone(
                    """
                    SELECT id
                    FROM users
                    WHERE email=%s AND id<>%s
                    """,
                    (new_email, self.user["id"])
                )

                if existing:
                    messagebox.showerror(
                        "Profile",
                        "This email is already being used."
                    )
                    return

                self.db.execute(
                    """
                    UPDATE users
                    SET name=%s, email=%s
                    WHERE id=%s
                    """,
                    (new_name, new_email, self.user["id"])
                )

                self.user["name"] = new_name
                self.user["email"] = new_email

                messagebox.showinfo(
                    "Profile",
                    "Profile updated successfully."
                )

                self.profile()

            except Exception as e:
                self.db_error(e)

        self.yellow_button(
            info,
            "SAVE PROFILE",
            save_profile
        ).pack(
            anchor="e",
            padx=25,
            pady=(5, 18),
            ipadx=15,
            ipady=7
        )

        # --------------------------------------------------------
        # Account overview
        # --------------------------------------------------------

        overview = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        overview.pack(fill="x", pady=(0, 15))

        tk.Label(
            overview,
            text="Account Overview",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(anchor="w", padx=25, pady=(18, 12))

        stats = tk.Frame(overview, bg=WHITE)
        stats.pack(fill="x", padx=20, pady=(0, 18))

        transaction_count = self.db.fetchone(
            """
            SELECT COUNT(*) total
            FROM transactions
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )["total"]

        account_count = self.db.fetchone(
            """
            SELECT COUNT(*) total
            FROM accounts
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )["total"]

        goal_count = self.db.fetchone(
            """
            SELECT COUNT(*) total
            FROM financial_goals
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )["total"]

        for title, value, accent in [
            ("Transactions", str(transaction_count), BLUE),
            ("Accounts", str(account_count), GREEN),
            ("Financial Goals", str(goal_count), YELLOW)
        ]:

            card = self.card(
                stats,
                title,
                value,
                accent
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 10)
            )

        # --------------------------------------------------------
        # Security
        # --------------------------------------------------------

        security = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#E6E6E6",
            highlightthickness=1
        )
        security.pack(fill="x")

        # Security header row
        security_header = tk.Frame(
            security,
            bg=WHITE
        )
        security_header.pack(
            fill="x",
            padx=25,
            pady=(18, 8)
        )

        tk.Label(
            security_header,
            text="Security",
            font=("Segoe UI", 15, "bold"),
            bg=WHITE,
            fg=DARK
        ).pack(side="left")

        # CHANGE PASSWORD button is placed beside the Security heading.
        password_visible = [False]

        # This frame remains hidden until CHANGE PASSWORD is clicked.
        password_area = tk.Frame(
            security,
            bg=WHITE
        )

        def show_change_password():

            if password_visible[0]:
                return

            password_visible[0] = True

            password_area.pack(
                fill="x",
                padx=17,
                pady=(5, 10)
            )

            old_password = tk.StringVar()
            new_password = tk.StringVar()
            confirm_password = tk.StringVar()

            # Current password
            old_box = tk.Frame(
                password_area,
                bg=WHITE
            )
            old_box.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=8,
                pady=5
            )

            tk.Label(
                old_box,
                text="Current Password",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            old_entry = ttk.Entry(
                old_box,
                textvariable=old_password,
                show="*",
                font=("Segoe UI", 10)
            )
            old_entry.pack(
                fill="x",
                ipady=5,
                pady=(3, 0)
            )

            # New password
            new_box = tk.Frame(
                password_area,
                bg=WHITE
            )
            new_box.grid(
                row=0,
                column=1,
                sticky="ew",
                padx=8,
                pady=5
            )

            tk.Label(
                new_box,
                text="New Password",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                new_box,
                textvariable=new_password,
                show="*",
                font=("Segoe UI", 10)
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 0)
            )

            # Confirm password
            confirm_box = tk.Frame(
                password_area,
                bg=WHITE
            )
            confirm_box.grid(
                row=1,
                column=0,
                sticky="ew",
                padx=8,
                pady=5
            )

            tk.Label(
                confirm_box,
                text="Confirm New Password",
                bg=WHITE,
                fg=GREY
            ).pack(anchor="w")

            ttk.Entry(
                confirm_box,
                textvariable=confirm_password,
                show="*",
                font=("Segoe UI", 10)
            ).pack(
                fill="x",
                ipady=5,
                pady=(3, 0)
            )

            password_area.grid_columnconfigure(0, weight=1)
            password_area.grid_columnconfigure(1, weight=1)

            actions = tk.Frame(
                password_area,
                bg=WHITE
            )
            actions.grid(
                row=1,
                column=1,
                sticky="e",
                padx=8,
                pady=5
            )

            def change_password():

                current = old_password.get()
                new = new_password.get()
                confirm = confirm_password.get()

                if not current or not new or not confirm:
                    messagebox.showwarning(
                        "Password",
                        "Please complete all password fields."
                    )
                    return

                if not verify_password(
                    current,
                    self.user["password_hash"]
                ):
                    messagebox.showerror(
                        "Password",
                        "Current password is incorrect."
                    )
                    return

                if len(new) < 6:
                    messagebox.showwarning(
                        "Password",
                        "New password must contain at least 6 characters."
                    )
                    return

                if new != confirm:
                    messagebox.showwarning(
                        "Password",
                        "New passwords do not match."
                    )
                    return

                try:

                    new_hash = hash_password(new)

                    self.db.execute(
                        """
                        UPDATE users
                        SET password_hash=%s
                        WHERE id=%s
                        """,
                        (new_hash, self.user["id"])
                    )

                    self.user["password_hash"] = new_hash

                    messagebox.showinfo(
                        "Password",
                        "Password changed successfully."
                    )

                    password_area.pack_forget()
                    password_visible[0] = False

                except Exception as e:
                    self.db_error(e)

            def cancel_password():

                password_area.pack_forget()
                password_visible[0] = False

            self.yellow_button(
                actions,
                "UPDATE PASSWORD",
                change_password
            ).pack(
                side="left",
                padx=5,
                ipadx=10,
                ipady=6
            )

            ttk.Button(
                actions,
                text="Cancel",
                command=cancel_password
            ).pack(
                side="left",
                padx=5
            )

            old_entry.focus_set()

        change_button = self.yellow_button(
            security_header,
            "CHANGE PASSWORD",
            show_change_password
        )
        change_button.pack(
            side="right",
            ipadx=15,
            ipady=7
        )

        tk.Label(
            security,
            text="Change your account password securely.",
            font=("Segoe UI", 10),
            bg=WHITE,
            fg=GREY
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 12)
        )



    def db_error(self, error):

        messagebox.showerror(
            "Database / Application Error",
            f"{error}\n\n"
            "Check that MySQL is running and your .env "
            "settings are correct."
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = App()

    app.mainloop()