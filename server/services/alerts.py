# server/services/alerts.py

import logging
import smtplib
from email.message import EmailMessage
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_enabled = config.get('ALERT_EMAIL_ENABLED', False)
        self.slack_enabled = config.get('ALERT_SLACK_ENABLED', False)
        
        if self.email_enabled:
            self.smtp_host = config.get('SMTP_HOST')
            self.smtp_port = config.get('SMTP_PORT')
            self.smtp_user = config.get('SMTP_USER')
            self.smtp_pass = config.get('SMTP_PASS')
            self.alert_email = config.get('ALERT_EMAIL')
        
        if self.slack_enabled:
            self.slack_webhook = config.get('SLACK_WEBHOOK_URL')

    def handle_alert(self, alert: Dict[str, Any]):
        """Process alert based on type"""
        try:
            if alert['type'] == 'job_failed':
                self._handle_job_failure(alert)
            # Add other alert types as needed
            
        except Exception as e:
            logger.error(f"Error handling alert: {str(e)}")

    def _handle_job_failure(self, alert: Dict[str, Any]):
        """Handle job failure alerts"""
        message = (
            f"Job Failed\n"
            f"Job ID: {alert['job_id']}\n"
            f"Error: {alert.get('error', 'Unknown error')}\n"
            f"Retries: {alert.get('retries', 0)}"
        )

        if self.email_enabled:
            self._send_email("Job Failure Alert", message)
        
        if self.slack_enabled:
            self._send_slack(message)

    def _send_email(self, subject: str, message: str):
        """Send email alert"""
        try:
            msg = EmailMessage()
            msg.set_content(message)
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")

    def _send_slack(self, message: str):
        """Send Slack alert"""
        try:
            requests.post(self.slack_webhook, json={'text': message})
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")