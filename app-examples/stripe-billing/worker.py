# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from activities import charge_customer, send_invoice_email
from workflows import SubscriptionWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="billing-task-queue",
        workflows=[SubscriptionWorkflow],
        activities=[charge_customer, send_invoice_email],
    )
    
    print("👷 [Worker] Listening for billing tasks on 'billing-task-queue'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
