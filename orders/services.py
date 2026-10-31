import hashlib
import hmac
import logging
from django.conf import settings
import razorpay
from razorpay.errors import SignatureVerificationError

logger = logging.getLogger(__name__)


class RazorpayService:
    """
    Encapsulates all Razorpay payment processing, order creation,
    cryptographic signature verification, and webhook validation.
    """

    @staticmethod
    def is_configured() -> bool:
        """Checks whether valid Razorpay credentials have been provided in environment/settings."""
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
        if not key_id or not key_secret:
            return False
        # Disallow default unconfigured placeholder values
        placeholder_tokens = ['YourKey', 'CHANGE_ME', 'placeholder', 'xxx', 'YourWebhook']
        if any(token in key_id for token in placeholder_tokens):
            return False
        if any(token in key_secret for token in placeholder_tokens):
            return False
        return True

    @classmethod
    def get_client(cls):
        """Initializes and returns an authenticated Razorpay client."""
        if not cls.is_configured():
            return None
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @classmethod
    def create_razorpay_order(cls, order) -> dict:
        """
        Creates a payment order on Razorpay servers using server-calculated
        amounts in paise (1 INR = 100 paise) and order number receipt.
        """
        client = cls.get_client()
        if not client:
            raise ValueError("Razorpay is not configured with valid API keys.")

        amount_paise = order.amount_in_paise
        receipt = order.order_number

        notes = {
            'order_number': order.order_number,
            'customer_email': order.email,
            'customer_name': order.full_name,
        }

        data = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': receipt,
            'notes': notes,
            'payment_capture': 1,  # Auto-capture upon successful authorization
        }

        rzp_order = client.order.create(data=data)
        order.razorpay_order_id = rzp_order.get('id')
        order.save(update_fields=['razorpay_order_id'])
        return rzp_order

    @classmethod
    def verify_signature(cls, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Cryptographically verifies Razorpay HMAC SHA256 payment signature.
        Never trusts client-reported payment success without valid signature.
        Uses Razorpay's official SDK client.utility.verify_payment_signature.
        """
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
        if not key_secret:
            logger.error("Signature verification failed: RAZORPAY_KEY_SECRET is not configured.")
            return False

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            logger.warning("Signature verification failed: Missing required signature parameters.")
            return False

        params_dict = {
            'razorpay_order_id': str(razorpay_order_id).strip(),
            'razorpay_payment_id': str(razorpay_payment_id).strip(),
            'razorpay_signature': str(razorpay_signature).strip(),
        }

        try:
            # Official Razorpay SDK verification method
            client = razorpay.Client(auth=(key_id or 'dummy_key_id', key_secret))
            client.utility.verify_payment_signature(params_dict)
            return True
        except SignatureVerificationError as e:
            logger.warning("Razorpay SDK signature verification failed: invalid digital signature (%s)", e)
            return False
        except Exception as e:
            logger.error("Unexpected error during SDK verification: %s. Performing RFC 2104 fallback HMAC.", e)
            # RFC 2104 constant-time HMAC SHA256 fallback
            msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
            generated = hmac.new(key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated, razorpay_signature)

    @classmethod
    def verify_webhook_signature(cls, payload_body: bytes, webhook_signature: str) -> bool:
        """Verifies webhook signature using configured webhook secret and official Razorpay SDK."""
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '').strip()
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
        if not webhook_secret or not webhook_signature:
            return False

        try:
            client = razorpay.Client(auth=(key_id or 'dummy_key_id', webhook_secret))
            body_str = payload_body.decode('utf-8') if isinstance(payload_body, bytes) else str(payload_body)
            client.utility.verify_webhook_signature(
                body_str,
                webhook_signature,
                webhook_secret
            )
            return True
        except SignatureVerificationError:
            logger.warning("Razorpay webhook signature verification failed.")
            return False
        except Exception as e:
            logger.error("Unexpected error during SDK webhook verification: %s. Using fallback HMAC.", e)
            body_bytes = payload_body if isinstance(payload_body, bytes) else payload_body.encode('utf-8')
            generated = hmac.new(webhook_secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated, webhook_signature)

