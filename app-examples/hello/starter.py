# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from datetime import timedelta
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, ScheduleOverlapPolicy, SchedulePolicy

# Import the Workflow class just for the Type hint/reference
# In a real project, you'd import this from a shared 'definitions' file
from worker import CronWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    schedule_id = "separated-cron-job"
    
    # Check if schedule exists, if so, delete it to start fresh
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
    except Exception:
        pass

    # Create the Schedule using the Client
    await client.create_schedule(
        schedule_id,
        Schedule(
            spec=ScheduleSpec(
                # Run every 30 seconds so the 20s task has time to finish!
                intervals=[ScheduleIntervalSpec(every=timedelta(seconds=30))]
            ),
            action=ScheduleActionStartWorkflow(
                CronWorkflow.run,
                1,
                id="separated-workflow-id",
                task_queue="cron-task-queue",
            ),
            policy=SchedulePolicy(
                overlap=ScheduleOverlapPolicy.CANCEL_OTHER,
            ),
        ),
    )

    print(f"🚀 [STARTER] Schedule '{schedule_id}' registered on the server.")
    print("👋 [STARTER] My job is done. I am exiting now.")

if __name__ == "__main__":
    asyncio.run(main())
