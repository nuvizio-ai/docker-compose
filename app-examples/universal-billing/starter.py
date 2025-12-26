import asyncio
from temporalio.client import Client
from workflows import UniversalBillingWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    # Example 1: Single Purchase via Stripe
    print("🚀 [Starter] Triggering Stripe Purchase...")
    handle = await client.start_workflow(
        UniversalBillingWorkflow.run,
        args=["user_abc", 4999, "stripe"],
        id="stripe-purchase-1",
        task_queue="universal-billing-queue",
    )
    print(f"✅ Started! View at: http://localhost:8080/namespaces/default/workflows/{handle.id}")

    # Example 2: PayPal Purchase
    print("🚀 [Starter] Triggering PayPal Purchase...")
    handle2 = await client.start_workflow(
        UniversalBillingWorkflow.run,
        args=["user_xyz", 1500, "paypal"],
        id="paypal-purchase-1",
        task_queue="universal-billing-queue",
    )
    print(f"✅ Started! View at: http://localhost:8080/namespaces/default/workflows/{handle2.id}")

if __name__ == "__main__":
    asyncio.run(main())
