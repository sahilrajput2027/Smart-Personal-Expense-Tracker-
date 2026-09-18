import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.config = DB_CONFIG.copy()

    def connect(self):
        return mysql.connector.connect(**self.config)

    def fetchone(self, query, params=()):
        conn = self.connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(query, params)
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def fetchall(self, query, params=()):
        conn = self.connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def execute(self, query, params=()):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute(query, params)
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def executemany(self, query, rows):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.executemany(query, rows)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def transfer(self, user_id, from_id, to_id, amount, date_value, description):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute(
                """SELECT id, account_name,
                   opening_balance + COALESCE((
                       SELECT SUM(
                           CASE
                             WHEN t.transaction_type='INCOME' AND t.account_id=a.id THEN t.amount
                             WHEN t.transaction_type='EXPENSE' AND t.account_id=a.id THEN -t.amount
                             WHEN t.transaction_type='TRANSFER' AND t.from_account_id=a.id THEN -t.amount
                             WHEN t.transaction_type='TRANSFER' AND t.to_account_id=a.id THEN t.amount
                             ELSE 0
                           END
                       ) FROM transactions t
                       WHERE t.user_id=a.user_id AND (t.account_id=a.id OR t.from_account_id=a.id OR t.to_account_id=a.id)
                   ),0) AS balance
                   FROM accounts a
                   WHERE a.id=%s AND a.user_id=%s
                   FOR UPDATE""",
                (from_id, user_id),
            )
            source = cur.fetchone()
            if not source:
                raise ValueError("Source account not found.")
            if float(source[2]) < amount:
                raise ValueError("Insufficient balance in the source account.")

            cur.execute(
                """INSERT INTO transactions
                   (user_id, account_id, category_id, transaction_type, amount,
                    transaction_date, description, payment_method, notes,
                    from_account_id, to_account_id)
                   VALUES (%s,NULL,NULL,'TRANSFER',%s,%s,%s,'Transfer','',%s,%s)""",
                (user_id, amount, date_value, description, from_id, to_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
