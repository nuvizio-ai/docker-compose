# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
import sys
from temporalio.client import Client
from workflows import SubscriptionWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    workflow_id = "billing-for-user@example.com"

    print(f"🛑 [Signal] Sending cancellation signal to {workflow_id}...")

    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(SubscriptionWorkflow.cancel_subscription)
        print("✅ [Signal] Cancellation signal received by Temporal.")
    except Exception as e:
        print(f"❌ [Signal] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
