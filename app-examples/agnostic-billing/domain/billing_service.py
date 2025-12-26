from .interfaces import PaymentGateway, LedgerRepository, ChargeRequest

class BillingService:
    """
    Pure business logic for a billing transaction.
    This class has NO dependency on Temporal or any other workflow engine.
    """
    def __init__(self, gateway: PaymentGateway, ledger: LedgerRepository):
        self.gateway = gateway
        self.ledger = ledger

    async def execute_checkout(self, customer_id: str, amount: int) -> str:
        # 1. Start local record
        local_id = await self.ledger.create_transaction(customer_id, amount)
        
        # 2. Charge external provider
        # We use the local_id as the idempotency key!
        try:
            gateway_id = await self.gateway.process_payment(
                ChargeRequest(customer_id, amount, idempotency_key=f"tx-{local_id}")
            )
            
            # 3. Success update
            await self.ledger.finalize_transaction(local_id, gateway_id, "succeeded")
            return gateway_id

        except Exception as e:
            # 4. Error update
            await self.ledger.finalize_transaction(local_id, "FAILED", "failed")
            raise e
