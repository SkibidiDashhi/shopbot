import sqlite3

# ================= DATABASE SETUP =================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()


# ================= USER FUNCTIONS =================
def add_user(user_id: int):
    """Add a user if not exists"""
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def get_balance(user_id: int) -> int:
    """Return user's balance"""
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return 0


def add_balance(user_id: int, amount: int):
    """Add Kyat to user's balance"""
    add_user(user_id)
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()


def deduct_balance(user_id: int, amount: int) -> bool:
    """Deduct Kyat from user's balance if enough funds"""
    balance = get_balance(user_id)
    if balance >= amount:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        return True
    return False
