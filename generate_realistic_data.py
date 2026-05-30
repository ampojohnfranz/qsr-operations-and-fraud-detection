import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

stores = ['Store 1', 'Store 2', 'Store 3', 'Store 4', 'Store 5', 'Store 6']
payment_methods = ['Cash', 'Credit Card', 'Mobile App']
cashiers = list(range(100, 111))  # 11 cashiers

# Suspicious cashiers — these two will have patterns
BAD_CASHIER_1 = 103  # excessive voids, works late shifts
BAD_CASHIER_2 = 107  # high refunds + discounts, Store 2

START_DATE = datetime(2026, 5, 1)

rows = []
txn_id = 10000

def make_txn(store, cashier, txn_type, payment, amount, timestamp):
    global txn_id
    row = {
        'Transaction_ID': f'TXN-{txn_id}',
        'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'Store': store,
        'Cashier_ID': cashier,
        'Transaction_Type': txn_type,
        'Payment_Method': payment,
        'Amount_USD': round(amount, 2)
    }
    txn_id += 1
    return row

# ── Generate normal transactions (majority) ────────────────────────────────────
for _ in range(9200):
    store = random.choice(stores)
    cashier = random.choice([c for c in cashiers if c not in [BAD_CASHIER_1, BAD_CASHIER_2]])
    day = random.randint(0, 29)
    # Normal hours: 7AM to 10PM
    hour = random.randint(7, 21)
    minute = random.randint(0, 59)
    ts = START_DATE + timedelta(days=day, hours=hour, minutes=minute)
    payment = random.choices(payment_methods, weights=[0.3, 0.45, 0.25])[0]

    # 90% completed, 5% void, 3% refund, 2% discount
    txn_type = random.choices(
        ['Completed', 'Void', 'Refund', 'Discount applied'],
        weights=[0.90, 0.05, 0.03, 0.02]
    )[0]

    if txn_type == 'Completed':
        amount = round(random.uniform(5, 45), 2)
    elif txn_type == 'Void':
        amount = round(random.uniform(5, 35), 2)
    elif txn_type == 'Refund':
        amount = round(random.uniform(5, 25), 2)  # normal refunds stay low
    else:
        amount = round(random.uniform(5, 40), 2)

    rows.append(make_txn(store, cashier, txn_type, payment, amount, ts))

# ── BAD CASHIER 1 (103) — excessive voids, late night, Store 3 ────────────────
# Works late shifts, does 8-12 voids per shift on certain days
for day in range(30):
    # Works evening shift most days
    base_hour = random.choices([16, 17, 18], weights=[0.3, 0.4, 0.3])[0]

    # Normal completed transactions during shift
    for _ in range(random.randint(15, 25)):
        hour = random.randint(base_hour, 21)
        ts = START_DATE + timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
        rows.append(make_txn('Store 3', BAD_CASHIER_1, 'Completed',
                              random.choice(payment_methods),
                              round(random.uniform(5, 40), 2), ts))

    # Suspicious voids — clusters on certain days
    if day % 4 == 0:  # every 4 days, excessive voiding
        num_voids = random.randint(7, 11)
        for _ in range(num_voids):
            hour = random.randint(21, 23)  # late at night
            ts = START_DATE + timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
            rows.append(make_txn('Store 3', BAD_CASHIER_1, 'Void', 'Cash',
                                  round(random.uniform(20, 45), 2), ts))

    # Occasional late night refunds
    if day % 7 == 0:
        ts = START_DATE + timedelta(days=day, hours=23, minutes=random.randint(0, 59))
        rows.append(make_txn('Store 3', BAD_CASHIER_1, 'Refund', 'Cash',
                              round(random.uniform(35, 45), 2), ts))

# ── BAD CASHIER 2 (107) — high refunds + discounts, Store 2 ──────────────────
# Processes suspiciously high refunds and gives out lots of discounts
for day in range(30):
    base_hour = random.choices([9, 10, 11], weights=[0.3, 0.4, 0.3])[0]

    # Normal transactions
    for _ in range(random.randint(12, 20)):
        hour = random.randint(base_hour, 17)
        ts = START_DATE + timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
        rows.append(make_txn('Store 2', BAD_CASHIER_2, 'Completed',
                              random.choice(payment_methods),
                              round(random.uniform(5, 40), 2), ts))

    # High value refunds — above normal threshold
    if day % 3 == 0:
        for _ in range(random.randint(2, 4)):
            hour = random.randint(base_hour, 16)
            ts = START_DATE + timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
            rows.append(make_txn('Store 2', BAD_CASHIER_2, 'Refund',
                                  random.choice(['Cash', 'Credit Card']),
                                  round(random.uniform(32, 45), 2), ts))

    # Excessive discounts on certain days
    if day % 5 == 0:
        for _ in range(random.randint(6, 9)):
            hour = random.randint(base_hour, 16)
            ts = START_DATE + timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
            rows.append(make_txn('Store 2', BAD_CASHIER_2, 'Discount applied', 'Cash',
                                  round(random.uniform(15, 40), 2), ts))

# ── Shuffle and save ───────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df['Transaction_ID'] = [f'TXN-{10000+i}' for i in range(len(df))]

output = '/mnt/user-data/outputs/pos_transaction_logs_v2.csv'
df.to_csv(output, index=False)

# Quick summary
print(f"Total transactions: {len(df)}")
print(f"\nTransaction type breakdown:")
print(df['Transaction_Type'].value_counts())
print(f"\nCashier 103 transactions: {len(df[df['Cashier_ID']==103])}")
print(f"Cashier 107 transactions: {len(df[df['Cashier_ID']==107])}")
print(f"\nLate night (10PM-6AM) voids/refunds: {len(df[(df['Timestamp'].str[11:13].astype(int) >= 22) & (df['Transaction_Type'].isin(['Void','Refund']))])}")
