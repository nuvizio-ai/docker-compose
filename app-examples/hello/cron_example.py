# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from datetime import timedelta, datetime
from temporalio import activity, workflow
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, ScheduleOverlapPolicy, SchedulePolicy
from temporalio.worker import Worker

# --- 1. Define the Activity ---
@activity.defn
async def long_running_task(iteration: int) -> str:
    print(f"🏃 Starting long task for iteration {iteration}...")
    # Simulate a task that takes longer than the cron interval
    await asyncio.sleep(20) 
    return f"Iteration {iteration} finished at {datetime.now()}"

# --- 2. Define the Workflow ---
@workflow.defn
class CronWorkflow:
    @workflow.run
    async def run(self, iteration: int) -> str:
        return await workflow.execute_activity(
            long_running_task,
            iteration,
            start_to_close_timeout=timedelta(seconds=30),
        )

# --- 3. Main Logic ---
async def main():
    client = await Client.connect("localhost:7233")
    
    schedule_id = "cancel-other-cron-job"
    task_queue = "cron-task-queue"

    # Define the Schedule
    await client.create_schedule(
        schedule_id,
        Schedule(
            spec=ScheduleSpec(
                # Run every 10 seconds (for quick demonstration)
                intervals=[ScheduleIntervalSpec(every=timedelta(seconds=10))]
            ),
            action=ScheduleActionStartWorkflow(
                CronWorkflow.run,
                1, # Initial arg (this is a bit tricky with dynamic args in schedules)
                id="cron-workflow-id",
                task_queue=task_queue,
            ),
            policy=SchedulePolicy(
                # THIS IS THE KEY PART:
                # If a new job triggers while the old one is running,
                # the old one is Terminated/Cancelled immediately.
                overlap=ScheduleOverlapPolicy.CANCEL_OTHER,
            ),
        ),
    )

    print(f"📅 Schedule '{schedule_id}' created with CANCEL_OTHER policy.")

    # Start Worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[CronWorkflow],
        activities=[long_running_task],
    )
    
    print("👷 Worker started. Watch the logs to see the old job get cancelled!")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
