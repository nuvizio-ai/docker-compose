# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from datetime import timedelta, datetime
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

# --- 1. Define the Activity (The "Doing" part) ---
@activity.defn
async def long_running_task(iteration: int) -> str:
    print(f"🏃 [WORKER] Starting activity for iteration {iteration}...")
    try:
        for i in range(20):
            if activity.is_cancelled():
                raise asyncio.CancelledError("Cancelled by server")
            activity.heartbeat(f"At second {i}")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("👋 [WORKER] Activity was cancelled. Cleaning up...")
        raise
    
    return f"Finished at {datetime.now()}"

# --- 2. Define the Workflow (The "Orchestrator" part) ---
@workflow.defn
class CronWorkflow:
    @workflow.run
    async def run(self, iteration: int) -> str:
        return await workflow.execute_activity(
            long_running_task,
            iteration,
            start_to_close_timeout=timedelta(seconds=30),
        )

# --- 3. Run the Worker ---
async def main():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="cron-task-queue",
        workflows=[CronWorkflow],
        activities=[long_running_task],
    )
    
    print("👷 [WORKER] Listening for tasks on 'cron-task-queue'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
