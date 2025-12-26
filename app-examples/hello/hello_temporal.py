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
import random

"""
# 1. Define the Activity (The "Doing" part)
@activity.defn
async def greet_task(name: str) -> str:
    return f"Hello, {name}! This ran via Temporal + uv."
"""


@activity.defn
async def greet_task(name: str) -> str:
    # Simulate a 50% chance of failure
    if random.random() < 0.5:
        print("❌ Activity failed! Simulating a crash...")
        raise RuntimeWarning("API is down!")
    
    return f"Hello, {name}! This succeeded after retries."    

# 2. Define the Workflow (The "Orchestrator" part)
@workflow.defn
class MyFirstWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            greet_task,
            name,
            start_to_close_timeout=timedelta(seconds=10),
        )

# 3. Main execution logic
async def main():
    # Connect to your local Temporal server
    client = await Client.connect("localhost:7233")

    # Start a Worker to process the tasks
    async with Worker(
        client,
        task_queue="uv-task-queue",
        workflows=[MyFirstWorkflow],
        activities=[greet_task],
    ):
        # Trigger the workflow
        result = await client.execute_workflow(
            MyFirstWorkflow.run,
            "Developer",
            id="uv-workflow-id",
            task_queue="uv-task-queue",
        )
        print(f"\n✅ Success: {result}")

if __name__ == "__main__":
    asyncio.run(main())