import sys
import os
from temporalio import activity

# Add domain to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from domain.interfaces import PaymentGateway, LedgerRepository, ChargeRequest
from domain.billing_service import BillingService

# --- Mock Implementations for Temporal ---
class TemporalStripeGateway(PaymentGateway):
    async def process_payment(self, request: ChargeRequest) -> str:
        # In a real app, this would use the 'stripe' library
        print(f"💳 [Activity] Gateway processing ${request.amount/100:.2f}")
        return f"gateway_ref_{request.idempotency_key}"

class TemporalPostgresLedger(LedgerRepository):
    async def create_transaction(self, customer_id: str, amount: int) -> str:
        # In a real app, this would use SQLAlchemy/Motor
        print(f"📝 [Activity] Ledger creating record for {customer_id}")
        return "local_db_999"

    async def finalize_transaction(self, local_id: str, gateway_id: str, status: str):
        print(f"📝 [Activity] Ledger finalizing {local_id} as {status}")

# --- Managed Activities ---
# These are just thin wrappers (Adapters)
@activity.defn
async def checkout_activity(customer_id: str, amount: int) -> str:
    # We instantiate the domain service inside the activity
    service = BillingService(TemporalStripeGateway(), TemporalPostgresLedger())
    
    # We delegate the core logic to the domain service
    return await service.execute_checkout(customer_id, amount)
