from datetime import timedelta
from temporalio import workflow
from .activities import checkout_activity

@workflow.defn
class AgnosticBillingWorkflow:
    @workflow.run
    async def run(self, customer_id: str, amount: int) -> str:
        # The workflow logic is now extremely simple.
        # It just manages the reliability of the checkout activity.
        return await workflow.execute_activity(
            checkout_activity,
            (customer_id, amount),
            start_to_close_timeout=timedelta(minutes=1),
        )
