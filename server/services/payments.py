# server/services/payments.py

from typing import Dict, Optional, Any, Tuple
import stripe
import logging
from models import User, CreditType

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, config: Dict[str, Any]):
        """
        PaymentService handles creation of Stripe Checkout sessions
        and processing webhook events.

        config is expected to have:
          - STRIPE_SECRET_KEY
          - STRIPE_WEBHOOK_SECRET
          - PRICING (dict of product_id -> { 'label', 'price_cents', 'credits': [...] })
          - BASE_URL (your front-end domain for success/cancel URLs)
        """
        self.config = config
        stripe.api_key = config['STRIPE_SECRET_KEY']
        self.webhook_secret = config['STRIPE_WEBHOOK_SECRET']
        self.pricing = config['PRICING']
        self.base_url = config.get('BASE_URL', 'http://localhost:3001')

    def create_checkout_session(self, user, product_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Stripe Checkout Session for the given product_id.
        Returns (session_url, error_message).
        """
        try:
            # Validate product
            if product_id not in self.pricing:
                return (None, f"Invalid product_id: {product_id}")

            product = self.pricing[product_id]
            price_cents = product['price_cents']
            label = product['label']
            credits = product['credits']  # e.g. [ { 'type': 'MODEL', 'quantity': 1 } ]

            # Build line item
            line_item = {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': price_cents,
                    'product_data': {
                        'name': label
                    },
                },
                'quantity': 1,
            }

            # Format the credits for metadata
            credits_str = self._format_credits_metadata(credits)
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[line_item],
                mode='payment',

                # Where user goes after success/cancel
                success_url=f"{self.base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.base_url}/payment/cancel",

                # Identify user and store product data
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
            logger.error(f"Stripe error: {e}", exc_info=True)
            return (None, "Payment processing error. Please try again.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return (None, "An error occurred while creating checkout session")

    def handle_webhook(self, payload: bytes, signature: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Handle Stripe webhook by verifying signature and parsing event.
        Returns (event_data, error) if successful or fails.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )

            # If it's a checkout completion event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']

                # e.g. "metadata" = { 'user_id': '1', 'product_id': 'PS_3PACK', 'credits': 'MODEL,1;PHOTOSHOOT,2' }
                user_id = int(session['metadata'].get('user_id', 0))
                product_id = session['metadata'].get('product_id')
                payment_intent_id = session.get('payment_intent')
                credits = self._parse_credits_metadata(session['metadata'].get('credits', ''))

                return ({
                    'type': 'checkout.session.completed',
                    'user_id': user_id,
                    'product_id': product_id,
                    'payment_intent_id': payment_intent_id,
                    'credits': credits
                }, None)

            # If it's some other event
            return ({'type': event['type']}, None)

        except stripe.error.SignatureVerificationError as e:
            logger.error("Invalid webhook signature", exc_info=True)
            return (None, "Invalid signature")
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return (None, "Webhook processing error")

    # Utility to turn [ { 'type': 'MODEL', 'quantity': 1 } ] => "MODEL,1;PHOTOSHOOT,2" for storing in metadata
    def _format_credits_metadata(self, credits: list) -> str:
        parts = []
        for c in credits:
            parts.append(f"{c['type']},{c['quantity']}")
        return ";".join(parts)

    # Utility to parse that metadata string back into a list of dicts with actual CreditType
    def _parse_credits_metadata(self, metadata_str: str) -> list:
        """
        e.g. "MODEL,1;PHOTOSHOOT,2" => [ { 'type': CreditType.MODEL, 'quantity': 1 }, ... ]
        """
        if not metadata_str:
            return []
        items = []
        for segment in metadata_str.split(';'):
            try:
                t, q = segment.split(',')
                # Convert 'MODEL' => CreditType.MODEL
                ctype = CreditType[t.strip()]
                qty = int(q.strip())
                items.append({ 'type': ctype, 'quantity': qty })
            except Exception as ex:
                logger.error(f"Failed to parse credit segment '{segment}': {ex}")
                continue
        return items
    
    def get_product_list(self):
        """
        Return a list of product data suitable for the frontend.
        e.g. [{ id: 'BUNDLE_MODEL_1_2PS', label: '1 Model + ...', price_cents: 1999 }, ... ]
        """
        products = []
        for pid, pdata in self.pricing.items():
            products.append({
                'id': pid,
                'label': pdata['label'],
                'price_cents': pdata['price_cents']
            })
        return products