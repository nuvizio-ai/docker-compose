import os
import stripe
from dataclasses import dataclass
from temporalio import activity
from dotenv import load_dotenv

# Load environment variables (STRIPE_API_KEY)
load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")

@dataclass
class PaymentDetails:
    customer_id: str
    amount: int
    currency: str = "usd"
    idempotency_key: str = ""

@activity.defn
async def charge_customer(details: PaymentDetails) -> str:
    if not stripe.api_key:
        raise ValueError("STRIPE_API_KEY environment variable is not set")

    activity.logger.info(f"Processing real Stripe payment for {details.customer_id}")

    try:
        # We use PaymentIntent (Modern Stripe API)
        # The 'idempotency_key' is the MOST IMPORTANT part here.
        # It's passed from the Workflow to ensure Temporal retries don't double charge.
        intent = stripe.PaymentIntent.create(
            amount=details.amount,
            currency=details.currency,
            customer=details.customer_id,
            payment_method="pm_card_visa", # Using Stripe's test visa card
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            idempotency_key=details.idempotency_key,
        )
        
        return intent.id

    except stripe.error.CardError as e:
        # Card declined is a "Permanent" error - we should probably fail the activity
        # and let the workflow handle the business logic (e.g. notify user)
        activity.logger.error(f"Card declined: {e.user_message}")
        raise e
    except stripe.error.StripeError as e:
        # Other stripe errors might be temporary (network, rate limit)
        # Temporal will automatically retry these!
        raise e

@activity.defn
async def send_invoice_email(email: str, payment_intent_id: str) -> bool:
    # In a real app, you'd use SendGrid, Mailchimp, etc.
    print(f"📧 [Email Service] Sending receipt for {payment_intent_id} to {email}")
    return True
