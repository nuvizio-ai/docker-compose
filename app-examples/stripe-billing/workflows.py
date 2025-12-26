from datetime import timedelta
from temporalio import workflow
from activities import PaymentDetails, charge_customer, send_invoice_email

@workflow.defn
class SubscriptionWorkflow:
    def __init__(self) -> None:
        self._cancelled = False
        self._period_count = 0

    @workflow.run
    async def run(self, email: str, customer_id: str, monthly_amount: int) -> str:
        workflow.logger.info(f"Starting subscription for {email}")

        # The billing loop
        # This while loop could theoretically run for years!
        while not self._cancelled:
            self._period_count += 1
            
            # --- 1. Charge the customer ---
            # We use the Workflow ID + Period Count as the Idempotency Key
            # This is the "Temporal Secret Sauce" for safe payments.
            idempotency_key = f"{workflow.info().workflow_id}-v{self._period_count}"
            
            payment_intent_id = await workflow.execute_activity(
                charge_customer,
                PaymentDetails(customer_id, monthly_amount, "usd", idempotency_key),
                start_to_close_timeout=timedelta(minutes=1),
            )

            # --- 2. Send the confirmation email ---
            await workflow.execute_activity(
                send_invoice_email,
                (email, payment_intent_id),
                start_to_close_timeout=timedelta(minutes=1),
            )

            # --- 3. Wait for the next billing cycle ---
            # In production, this would be timedelta(days=30)
            # For our demo, we wait 30 seconds.
            workflow.logger.info(f"Wait 30s for next billing cycle (Period {self._period_count} done)")
            
            # This wait is "Signal-aware". If we get a cancellation signal,
            # we will wake up immediately!
            await workflow.wait_condition(
                lambda: self._cancelled, 
                timeout=timedelta(seconds=30)
            )

        return f"Subscription ended after {self._period_count} periods."

    @workflow.signal
    def cancel_subscription(self) -> None:
        workflow.logger.info("Cancellation signal received!")
        self._cancelled = True

    @workflow.query
    def get_status(self) -> str:
        return f"Currently in Period {self._period_count}. Cancelled: {self._cancelled}"
