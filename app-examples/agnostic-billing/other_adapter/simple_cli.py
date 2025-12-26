import sys
import os
import asyncio

# Add domain to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from domain.interfaces import PaymentGateway, LedgerRepository, ChargeRequest
from domain.billing_service import BillingService

class SimpleConsoleGateway(PaymentGateway):
    async def process_payment(self, request: ChargeRequest) -> str:
        print(f"   [Console Gateway] 💳 Processing charging ${request.amount/100:.2f}...")
        return "console_ref_123"

class SimpleConsoleLedger(LedgerRepository):
    async def create_transaction(self, customer_id: str, amount: int) -> str:
        print(f"   [Console Ledger] 📓 Recording start for {customer_id}")
        return "console_db_id"

    async def finalize_transaction(self, local_id: str, gateway_id: str, status: str):
        print(f"   [Console Ledger] ✅ Finalized as {status}")

async def run_standalone_billing():
    print("🚀 Running Billing Service WITHOUT Temporal...")
    
    # 1. Wire up the generic service with Console adapters
    service = BillingService(SimpleConsoleGateway(), SimpleConsoleLedger())
    
    # 2. Run the logic
    # This is the EXACT SAME logic that the Temporal activity uses!
    result = await service.execute_checkout("cli_user", 1999)
    
    print(f"🔥 Successfully finished! Gateway ID: {result}")

if __name__ == "__main__":
    asyncio.run(run_standalone_billing())
