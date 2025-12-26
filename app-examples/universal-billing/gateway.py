from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class ProviderType(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANK = "bank"

@dataclass
class ChargeRequest:
    amount: int
    currency: str
    customer_id: str
    idempotency_key: str

class PaymentGateway(ABC):
    @abstractmethod
    async def charge(self, request: ChargeRequest) -> str:
        pass

    @abstractmethod
    async def refund(self, transaction_id: str, amount: int) -> bool:
        pass

# --- 1. Stripe Implementation ---
class StripeAdapter(PaymentGateway):
    async def charge(self, request: ChargeRequest) -> str:
        # Real logic: stripe.PaymentIntent.create(...)
        print(f"💳 [Stripe] Charging {request.amount} {request.currency}")
        return f"stripe_tx_{request.idempotency_key}"

    async def refund(self, transaction_id: str, amount: int) -> bool:
        print(f"💳 [Stripe] Refunding {transaction_id}")
        return True

# --- 2. PayPal Implementation ---
class PayPalAdapter(PaymentGateway):
    async def charge(self, request: ChargeRequest) -> str:
        # Real logic: paypal_sdk.CapturePayment(...)
        print(f"💰 [PayPal] Charging {request.amount} {request.currency}")
        return f"paypal_tx_{request.idempotency_key}"

    async def refund(self, transaction_id: str, amount: int) -> bool:
        print(f"💰 [PayPal] Refunding {transaction_id}")
        return True

def get_gateway(provider: ProviderType) -> PaymentGateway:
    if provider == ProviderType.STRIPE:
        return StripeAdapter()
    elif provider == ProviderType.PAYPAL:
        return PayPalAdapter()
    raise ValueError(f"Unsupported provider: {provider}")
