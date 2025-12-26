from datetime import datetime
from temporalio import activity
from gateway import ChargeRequest, ProviderType, get_gateway

# --- Ledger Activities ---
@activity.defn
async def record_transaction_start(customer_id: str, amount: int, provider: str) -> int:
    print(f"📝 [Ledger] Initializing transaction for {customer_id}: ${amount/100:.2f} via {provider}")
    return 12345 

@activity.defn
async def update_transaction_status(db_id: int, gateway_id: str, status: str):
    print(f"📝 [Ledger] Transaction {db_id} updated to {status} (Gateway Ref: {gateway_id})")

# --- Gateway Activities ---
@activity.defn
async def execute_gateway_charge(params: dict) -> str:
    # Convert dict back to dataclass
    request = ChargeRequest(
        amount=params["amount"],
        currency=params["currency"],
        customer_id=params["customer_id"],
        idempotency_key=params["idempotency_key"]
    )
    
    # In a real app, the provider choice is a variable
    provider = ProviderType.STRIPE 
    gateway = get_gateway(provider)
    
    return await gateway.charge(request)

@activity.defn
async def process_refund(transaction_id: str, amount: int) -> bool:
    gateway = get_gateway(ProviderType.STRIPE)
    return await gateway.refund(transaction_id, amount)
