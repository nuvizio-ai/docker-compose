from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ChargeRequest:
    customer_id: str
    amount: int
    idempotency_key: str

class PaymentGateway(ABC):
    @abstractmethod
    async def process_payment(self, request: ChargeRequest) -> str:
        """Processes a payment and returns a transaction ID."""
        pass

class LedgerRepository(ABC):
    @abstractmethod
    async def create_transaction(self, customer_id: str, amount: int) -> str:
        """Creates a pending transaction and returns its local ID."""
        pass

    @abstractmethod
    async def finalize_transaction(self, local_id: str, gateway_id: str, status: str):
        """Updates the transaction with the final status and gateway reference."""
        pass
