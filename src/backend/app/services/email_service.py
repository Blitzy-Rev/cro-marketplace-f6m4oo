"""
Email service module for the Molecular Data Management and CRO Integration Platform.

This module provides functionality for sending emails, including plain text, HTML, and
template-based emails. It supports both synchronous and asynchronous email sending 
with proper error handling and logging.
"""

import typing
from typing import Dict, List, Optional, Any
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jinja2
from pathlib import Path

from ..core.config import settings
from ..core.logging import get_logger
from ..tasks.celery_app import celery_app

# Set up logger
logger = get_logger(__name__)

# Define the template directory for email templates
TEMPLATE_DIR = Path(__file__).parent.parent / 'templates' / 'email'


def create_email_message(
    subject: str,
    body: str,
    to_email: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    is_html: bool = False
) -> MIMEMultipart:
    """
    Create an email message with proper headers and content.
    
    Args:
        subject: Email subject
        body: Email body content
        to_email: Recipient email address
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
        is_html: Whether the body is HTML formatted
    
    Returns:
        Prepared email message
    """
    # Use default sender details if not provided
    sender_email = from_email or settings.EMAILS_FROM_EMAIL
    sender_name = from_name or settings.EMAILS_FROM_NAME
    
    # Create a multipart message
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = to_email
    
    # Attach the body with appropriate content type
    content_type = "html" if is_html else "plain"
    message.attach(MIMEText(body, content_type))
    
    return message


def send_email(
    subject: str,
    body: str,
    to_email: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    is_html: bool = False
) -> bool:
    """
    Send an email synchronously.
    
    Args:
        subject: Email subject
        body: Email body content
        to_email: Recipient email address
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
        is_html: Whether the body is HTML formatted
    
    Returns:
        True if email was sent successfully
    """
    try:
        # Get email settings from application configuration
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        
        # Create the email message
        message = create_email_message(
            subject=subject,
            body=body,
            to_email=to_email,
            from_email=from_email,
            from_name=from_name,
            is_html=is_html
        )
        
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        # Send the email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_password)
            server.send_message(message)
            
        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
        return False


@celery_app.task(name='tasks.send_email_async', queue='email')
def send_email_async(
    subject: str,
    body: str,
    to_email: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    is_html: bool = False
) -> bool:
    """
    Send an email asynchronously using Celery.
    
    Args:
        subject: Email subject
        body: Email body content
        to_email: Recipient email address
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
        is_html: Whether the body is HTML formatted
    
    Returns:
        True if email task was queued successfully
    """
    logger.info(f"Sending email asynchronously to {to_email}: {subject}")
    return send_email(
        subject=subject,
        body=body,
        to_email=to_email,
        from_email=from_email,
        from_name=from_name,
        is_html=is_html
    )


def render_template(
    template_name: str, 
    context: Dict[str, Any]
) -> str:
    """
    Render an email template with provided context.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
    
    Returns:
        Rendered HTML content
    """
    template_path = TEMPLATE_DIR / template_name
    
    # Check if template file exists
    if not template_path.exists():
        error_msg = f"Email template not found: {template_name}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Create Jinja2 environment with template directory
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        autoescape=True
    )
    
    # Load template from file
    template = env.get_template(template_name)
    
    # Render template with provided context
    return template.render(**context)


def send_template_email(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    to_email: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send an email using a template.
    
    Args:
        subject: Email subject
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        to_email: Recipient email address
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
    
    Returns:
        True if email was sent successfully
    """
    # Render HTML content using render_template function
    html_content = render_template(template_name, context)
    
    # Call send_email function with rendered HTML content and is_html=True
    return send_email(
        subject=subject,
        body=html_content,
        to_email=to_email,
        from_email=from_email,
        from_name=from_name,
        is_html=True
    )


@celery_app.task(name='tasks.send_template_email_async', queue='email')
def send_template_email_async(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    to_email: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send a template-based email asynchronously using Celery.
    
    Args:
        subject: Email subject
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        to_email: Recipient email address
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
    
    Returns:
        True if email task was queued successfully
    """
    logger.info(f"Sending template email asynchronously to {to_email}: {subject}")
    return send_template_email(
        subject=subject,
        template_name=template_name,
        context=context,
        to_email=to_email,
        from_email=from_email,
        from_name=from_name
    )


def send_bulk_email(
    subject: str,
    body: str,
    to_emails: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    is_html: bool = False
) -> Dict[str, bool]:
    """
    Send the same email to multiple recipients.
    
    Args:
        subject: Email subject
        body: Email body content
        to_emails: List of recipient email addresses
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
        is_html: Whether the body is HTML formatted
    
    Returns:
        Dictionary mapping email addresses to success/failure status
    """
    # Initialize results dictionary
    results = {}
    
    # For each recipient email address:
    for email in to_emails:
        # Call send_email function with current recipient
        results[email] = send_email(
            subject=subject,
            body=body,
            to_email=email,
            from_email=from_email,
            from_name=from_name,
            is_html=is_html
        )
    
    # Log overall bulk email results
    success_count = sum(1 for status in results.values() if status)
    logger.info(f"Bulk email sent: {success_count}/{len(to_emails)} successful")
    
    # Return results dictionary
    return results


@celery_app.task(name='tasks.send_bulk_email_async', queue='email')
def send_bulk_email_async(
    subject: str,
    body: str,
    to_emails: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    is_html: bool = False
) -> bool:
    """
    Send the same email to multiple recipients asynchronously.
    
    Args:
        subject: Email subject
        body: Email body content
        to_emails: List of recipient email addresses
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
        is_html: Whether the body is HTML formatted
    
    Returns:
        True if all email tasks were queued successfully
    """
    logger.info(f"Sending bulk email asynchronously to {len(to_emails)} recipients: {subject}")
    
    # For each recipient email address:
    for email in to_emails:
        # Call send_email_async.delay() with current recipient
        send_email_async.delay(
            subject=subject,
            body=body,
            to_email=email,
            from_email=from_email,
            from_name=from_name,
            is_html=is_html
        )
    
    # Return True if all tasks were queued successfully
    return True


def send_bulk_template_email(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    to_emails: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict[str, bool]:
    """
    Send a template-based email to multiple recipients.
    
    Args:
        subject: Email subject
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        to_emails: List of recipient email addresses
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
    
    Returns:
        Dictionary mapping email addresses to success/failure status
    """
    # Render HTML content using render_template function
    html_content = render_template(template_name, context)
    
    # Initialize results dictionary
    results = {}
    
    # For each recipient email address:
    for email in to_emails:
        # Call send_email function with rendered HTML content and is_html=True
        results[email] = send_email(
            subject=subject,
            body=html_content,
            to_email=email,
            from_email=from_email,
            from_name=from_name,
            is_html=True
        )
    
    # Log overall bulk template email results
    success_count = sum(1 for status in results.values() if status)
    logger.info(f"Bulk template email sent: {success_count}/{len(to_emails)} successful")
    
    # Return results dictionary
    return results


@celery_app.task(name='tasks.send_bulk_template_email_async', queue='email')
def send_bulk_template_email_async(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    to_emails: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send a template-based email to multiple recipients asynchronously.
    
    Args:
        subject: Email subject
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        to_emails: List of recipient email addresses
        from_email: Sender email address (defaults to settings)
        from_name: Sender name (defaults to settings)
    
    Returns:
        True if all email tasks were queued successfully
    """
    logger.info(f"Sending bulk template email asynchronously to {len(to_emails)} recipients: {subject}")
    
    # For each recipient email address:
    for email in to_emails:
        # Call send_template_email_async.delay() with current recipient
        send_template_email_async.delay(
            subject=subject,
            template_name=template_name,
            context=context,
            to_email=email,
            from_email=from_email,
            from_name=from_name
        )
    
    # Return True if all tasks were queued successfully
    return True