from datetime import timedelta
from temporalio import workflow
from activities import record_transaction_start, update_transaction_status, execute_gateway_charge

@workflow.defn
class UniversalBillingWorkflow:
    @workflow.run
    async def run(self, 
                  customer_id: str, 
                  amount: int, 
                  provider: str) -> str:
        
        # 1. Record the start in our LOCAL Ledger
        db_id = await workflow.execute_activity(
            record_transaction_start,
            (customer_id, amount, provider),
            start_to_close_timeout=timedelta(seconds=5),
        )

        # 2. Charge the External Gateway
        # Note: We use the DB_ID as the idempotency key!
        idempotency_key = f"db-{db_id}"
        
        gateway_tx_id = await workflow.execute_activity(
            execute_gateway_charge,
            {
                "amount": amount,
                "currency": "usd",
                "customer_id": customer_id,
                "idempotency_key": idempotency_key
            },
            start_to_close_timeout=timedelta(minutes=1),
        )

        # 3. Update the Local Ledger with success
        await workflow.execute_activity(
            update_transaction_status,
            (db_id, gateway_tx_id, "succeeded"),
            start_to_close_timeout=timedelta(seconds=5),
        )

        return f"Payment Success. Ledger DB ID: {db_id}, Gateway ID: {gateway_tx_id}"
