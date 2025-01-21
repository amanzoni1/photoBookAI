# server/services/emailer.py

import logging
from typing import Dict, Any, Optional, List
import resend
from pathlib import Path
import jinja2

logger = logging.getLogger(__name__)

class EmailException(Exception):
    """Custom exception for email-related errors."""
    pass

class EmailService:
    """
    Provides functionality to send emails using Resend. 
    Uses Jinja2 templates located in EMAIL_TEMPLATES_DIR.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email service with configuration.

        config is expected to have:
          - RESEND_API_KEY: API key for Resend
          - EMAIL_FROM: Default sender email address
          - EMAIL_TEMPLATES_DIR: Path to email templates directory
          - FRONTEND_URL: Base URL for links in emails
        """
        self.config = config
        self.api_key = config.get('RESEND_API_KEY')
        self.from_email = config.get('EMAIL_FROM', 'noreply@example.com')
        self.frontend_url = config.get('FRONTEND_URL', 'http://localhost:3001')
        self.templates_dir = Path(config.get('EMAIL_TEMPLATES_DIR', 'services/templates/email'))

        if not self.api_key:
            logger.warning("No RESEND_API_KEY found in config. Emails will fail unless provided.")
        resend.api_key = self.api_key  # Initialize Resend client

        # Initialize Jinja2 environment for HTML templates
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render an HTML email template with the given context.

        template_name: Name of the template without '.html' (e.g. 'welcome').
        context:       Dictionary of template variables.
        """
        try:
            template_file = self.templates_dir / f"{template_name}.html"
            if not template_file.is_file():
                msg = f"Template file not found: {template_file}"
                logger.error(msg)
                raise EmailException(msg)

            template = self.template_env.get_template(f"{template_name}.html")
            return template.render(**context)

        except jinja2.TemplateError as e:
            logger.error(f"Jinja2 template rendering failed: {str(e)}")
            raise EmailException(f"Failed to render template '{template_name}': {str(e)}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email using Resend with an HTML template.

        Args:
            to_email:      Recipient email address
            subject:       Email subject
            template_name: Name of the template to load (without '.html')
            context:       Data for rendering the template
            cc:            Optional list of CC addresses
            reply_to:      Optional reply-to email address

        Returns:
            True if sent successfully, otherwise raises EmailException.
        """
        try:
            logger.info(f"Preparing to send '{template_name}' email to {to_email}.")
            logger.debug(f"Email context: {context}")

            # Render the HTML content
            html_content = self._render_template(template_name, context)

            # Build payload for Resend
            params = {
                'from': self.from_email,
                'to': to_email,
                'subject': subject,
                'html': html_content,
            }
            if cc:
                params['cc'] = cc
            if reply_to:
                params['reply_to'] = reply_to

            logger.debug(f"Sending email via Resend with params: {params}")
            response = resend.Emails.send(params)
            logger.debug(f"Resend API response: {response}")

            if response and response.get('id'):
                logger.info(f"Email sent successfully to {to_email} (Resend ID: {response['id']}).")
                return True
            else:
                msg = f"No email ID returned from Resend. Full response: {response}"
                logger.error(msg)
                raise EmailException(msg)

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            raise EmailException(f"Email sending failed to {to_email}: {str(e)}")

    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Send a welcome email to a new user.
        """
        context = {
            'user_name': user_name,
            'login_url': f"{self.frontend_url}/login"
        }
        return self.send_email(
            to_email=user_email,
            subject="Welcome to AI Training Platform",
            template_name="welcome",
            context=context
        )

    def send_purchase_confirmation(
        self,
        user_email: str,
        user_name: str,
        product_name: str,
        product_id: str,
        amount: float,
        credits: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Send a purchase confirmation email with product/credit details.
        """
        context = {
            'user_name': user_name,
            'product_name': product_name,
            'product_id': product_id,
            'amount': amount,  # in cents
            'amount_usd': f"${amount / 100:.2f}",
            'credits': credits,
            'dashboard_url': f"{self.frontend_url}/dashboard"
        }

        return self.send_email(
            to_email=user_email,
            subject="Your Purchase Confirmation",
            template_name="purchase_confirmation",
            context=context
        )

    def send_training_complete(
        self,
        user_email: str,
        user_name: str,
        model_name: str,
        success: bool = True
    ) -> bool:
        """
        Send training completion notification.
        Currently, the template doesn't show model_name or time, so it's optional.
        """
        template = "training_complete" if success else "training_failed"

        context = {
            'user_name': user_name,
            'model_url': f"{self.config['FRONTEND_URL']}/models/{model_name}"  
        }

        subject = "Training Complete!"
        if not success:
            subject = "Training Failed"

        return self.send_email(
            to_email=user_email,
            subject=subject,
            template_name=template,
            context=context
        )