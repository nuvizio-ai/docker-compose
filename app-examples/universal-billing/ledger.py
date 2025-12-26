from datetime import datetime
from temporalio import activity

@activity.defn
async def record_transaction_start(customer_id: str, amount: int, provider: str) -> int:
    # In a real app: 
    # db.execute("INSERT INTO transactions (customer_id, amount, status) VALUES (?, ?, 'pending')", ...)
    print(f"📝 [Ledger] Initializing transaction for {customer_id}: ${amount/100:.2f} via {provider}")
    return 12345 # Mock DB ID

@activity.defn
async def update_transaction_status(db_id: int, gateway_id: str, status: str):
    # db.execute("UPDATE transactions SET status=?, gateway_id=?, completed_at=? WHERE id=?", ...)
    print(f"📝 [Ledger] Transaction {db_id} updated to {status} (Gateway Ref: {gateway_id})")

@activity.defn
async def fetch_customer_stats(customer_id: str) -> dict:
    # db.execute("SELECT SUM(amount) FROM transactions WHERE customer_id=?", customer_id)
    print(f"📊 [Stats] Fetching totals for {customer_id}...")
    return {"total_spent": 5998, "transaction_count": 2}
