import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from activities import record_transaction_start, update_transaction_status, execute_gateway_charge
from workflows import UniversalBillingWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="universal-billing-queue",
        workflows=[UniversalBillingWorkflow],
        activities=[record_transaction_start, update_transaction_status, execute_gateway_charge],
    )
    
    print("👷 [Worker] Universal Billing Engine started...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
