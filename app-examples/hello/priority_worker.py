# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

# --- Activities ---
@activity.defn
async def critical_payment(amount: int) -> str:
    return f"💳 High Priority: Processed ${amount}"

@activity.defn
async def background_log(message: str) -> str:
    return f"📄 Low Priority Log: {message}"

# --- Workflow ---
@workflow.defn
class PriorityWorkflow:
    @workflow.run
    async def run(self) -> list:
        # 1. Run critical task on the 'critical-queue'
        res1 = await workflow.execute_activity(
            critical_payment,
            100,
            task_queue="critical-queue",
            start_to_close_timeout=timedelta(seconds=5),
        )
        
        # 2. Run background task on the 'background-queue'
        res2 = await workflow.execute_activity(
            background_log,
            "User logged in",
            task_queue="background-queue",
            start_to_close_timeout=timedelta(seconds=5),
        )
        return [res1, res2]

async def main():
    client = await Client.connect("localhost:7233")

    # --- Start Two Different Workers ---
    # Worker 1: Only handles critical tasks
    critical_worker = Worker(
        client,
        task_queue="critical-queue",
        activities=[critical_payment],
    )

    # Worker 2: Only handles background tasks
    background_worker = Worker(
        client,
        task_queue="background-queue",
        activities=[background_log],
        workflows=[PriorityWorkflow], # Workflows usually live on one queue
    )

    # Run both workers simultaneously
    async with critical_worker, background_worker:
        result = await client.execute_workflow(
            PriorityWorkflow.run,
            id="priority-wf-id",
            task_queue="background-queue",
        )
        print(f"\n✅ Results: {result}")

if __name__ == "__main__":
    asyncio.run(main())