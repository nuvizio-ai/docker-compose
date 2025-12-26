# /// script
# dependencies = [
#   "temporalio",
# ]
# ///

import asyncio
from temporalio.client import Client
from temporalio.api.enums.v1 import TaskQueueType

async def main():
    client = await Client.connect("localhost:7233")
    
    # The name of the queue we want to check
    queue_name = "cron-task-queue"

    # 1. Call the 'describe_task_queue' API
    # This returns low-level info about the queue
    desc = await client.workflow_service.describe_task_queue(
        namespace="default",
        task_queue=queue_name,
        task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_ACTIVITY,
    )

    # 2. Check the backlog
    # Note: 'backlog_count_hint' is an APPROXIMATION. 
    # Temporal doesn't give an exact count because it's a distributed system, 
    # but it gives a 'hint' that is good enough for scaling.
    backlog = desc.task_queue_status.backlog_count_hint
    
    print(f"📊 Task Queue: {queue_name}")
    print(f"📈 Approximate Backlog: {backlog} tasks")
    
    if backlog > 0:
        print("⚠️  Warning: Queue is starting to pile up!")
    else:
        print("✅ Queue is healthy (no backlog).")

if __name__ == "__main__":
    asyncio.run(main())
