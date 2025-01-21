# server/services/payments.py

import logging
from typing import Dict, Optional, Any, Tuple

import stripe
from models import User, CreditType

logger = logging.getLogger(__name__)

class PaymentException(Exception):
    """Custom exception for payment-related errors."""
    pass

class PaymentService:
    """
    PaymentService handles creation of Stripe Checkout sessions and
    processing of webhook events. It also coordinates the sending of
    purchase confirmation emails.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PaymentService with necessary Stripe and application config.

        config is expected to have:
            STRIPE_SECRET_KEY
            STRIPE_WEBHOOK_SECRET
            PRICING (dict of product_id -> { 'label', 'price_cents', 'credits': [...] })
            FRONTEND_URL (base for success/cancel URLs)
        """
        self.config = config

        # Setup Stripe
        stripe.api_key = config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = config.get('STRIPE_WEBHOOK_SECRET')
        self.pricing = config.get('PRICING', {})
        self.base_url = config.get('FRONTEND_URL', 'http://localhost:3001')

    def create_checkout_session(self, user: User, product_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Stripe Checkout Session for the given product_id.

        Returns:
            (session_url, error_message)
        """
        try:
            if product_id not in self.pricing:
                return (None, f"Invalid product_id: {product_id}")

            product = self.pricing[product_id]
            price_cents = product['price_cents']
            label = product['label']
            credits = product['credits']  # e.g. [ { 'type': 'MODEL', 'quantity': 1 } ]

            # Build the line item
            line_item = {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': price_cents,
                    'product_data': {'name': label},
                },
                'quantity': 1
            }

            # Format the credits for metadata
            credits_str = self._format_credits_metadata(credits)

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[line_item],
                mode='payment',
                success_url=f"{self.base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.base_url}/payment/cancel",
                client_reference_id=str(user.id),
                metadata={
                    'user_id': str(user.id),
                    'product_id': product_id,
                    'credits': credits_str
                }
            )

            logger.info(f"Created checkout session {session.id} for user {user.id}, product={product_id}")
            return (session.url, None)

        except stripe.error.StripeError as e:
            logger.error("Stripe error creating session: %s", e, exc_info=True)
            return (None, "Payment processing error. Please try again.")
        except Exception as e:
            logger.error("Unexpected error creating checkout session: %s", e, exc_info=True)
            return (None, "An error occurred while creating checkout session")

    def handle_webhook(self,
                       payload: bytes,
                       signature: str,
                       email_service: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Handle Stripe webhook by verifying signature and parsing the event.

        Returns:
            (event_data, error_message)
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )

            event_type = event.get('type')
            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                user_id = int(session['metadata'].get('user_id', 0))
                product_id = session['metadata'].get('product_id')
                payment_intent_id = session.get('payment_intent')
                credits = self._parse_credits_metadata(session['metadata'].get('credits', ''))

                user = User.query.get(user_id)
                if user:
                    self._notify_purchase(
                        email_service=email_service,
                        user=user,
                        product_id=product_id,
                        credits_list=credits
                    )

                return ({
                    'type': 'checkout.session.completed',
                    'user_id': user_id,
                    'product_id': product_id,
                    'payment_intent_id': payment_intent_id,
                    'credits': credits
                }, None)

            # If it's some other event
            return ({'type': event_type}, None)

        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature", exc_info=True)
            return (None, "Invalid signature")
        except Exception as e:
            logger.error("Webhook processing error: %s", e, exc_info=True)
            return (None, "Webhook processing error")

    def get_product_list(self) -> list:
        """
        Return a list of product info suitable for the front-end.
        """
        products = []
        for pid, pdata in self.pricing.items():
            products.append({
                'id': pid,
                'label': pdata['label'],
                'price_cents': pdata['price_cents']
            })
        return products

    def _notify_purchase(self,
                         email_service: Any,
                         user: User,
                         product_id: str,
                         credits_list: list) -> None:
        """
        Send a purchase confirmation email after a checkout session completes.

        Args:
            email_service: EmailService instance
            user:          The User object
            product_id:    The purchased product ID
            credits_list:  The list of credit dictionaries
        """
        try:
            product = self.pricing[product_id]  # e.g., { 'label': '1 Model + 2 Photoshoots', ... }
            credits_details = {
                cinfo['type'].name: {
                    'quantity': cinfo['quantity'],
                    'type': cinfo['type'].name
                }
                for cinfo in credits_list
            }

            logger.debug("Sending purchase email with credits details: %s", credits_details)
            email_service.send_purchase_confirmation(
                user_email=user.email,
                user_name=user.username,
                product_name=product['label'],
                product_id=product_id,
                amount=product['price_cents'],
                credits=credits_details
            )
            logger.info("Purchase confirmation sent to %s for product %s", user.email, product_id)

        except Exception as e:
            logger.error("Failed to send purchase confirmation: %s", e, exc_info=True)
            logger.error("Email parameters => user=%s, product=%s", user.email, product_id)

    def _format_credits_metadata(self, credits: list) -> str:
        """
        Convert a list of credit dicts into a semicolon-delimited string.
        Example: [ { 'type': 'MODEL', 'quantity': 1 } ] -> 'MODEL,1'
        """
        parts = []
        for c in credits:
            parts.append(f"{c['type']},{c['quantity']}")
        return ";".join(parts)

    def _parse_credits_metadata(self, metadata_str: str) -> list:
        """
        Parse a semicolon-delimited string of 'TYPE,QUANTITY' into a list of credit dicts.
        e.g. "MODEL,1;PHOTOSHOOT,2" -> [ { 'type': CreditType.MODEL, 'quantity': 1 }, ... ]
        """
        if not metadata_str:
            return []
        items = []
        for segment in metadata_str.split(';'):
            try:
                t, q = segment.split(',')
                ctype = CreditType[t.strip()]
                qty = int(q.strip())
                items.append({'type': ctype, 'quantity': qty})
            except Exception as ex:
                logger.error("Failed to parse credit segment '%s': %s", segment, ex, exc_info=True)
        return items