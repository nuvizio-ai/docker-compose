# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
import uuid
from temporalio.client import Client
from workflows import SubscriptionWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    customer_email = "user@example.com"
    workflow_id = f"billing-for-{customer_email}"

    print(f"🚀 [Starter] Starting subscription for {customer_email}...")

    # Start the workflow
    handle = await client.start_workflow(
        SubscriptionWorkflow.run,
        args=["user@example.com", "cust_12345", 2999], # $29.99
        id=workflow_id,
        task_queue="billing-task-queue",
    )

    print(f"✅ [Starter] Subscription started. Workflow ID: {handle.id}")
    print(f"🔗 View in UI: http://localhost:8080/namespaces/default/workflows/{handle.id}")

if __name__ == "__main__":
    asyncio.run(main())
