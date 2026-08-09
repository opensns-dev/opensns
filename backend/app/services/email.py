import logging
from typing import Optional

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None,
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning(f"Email not sent to {to} - RESEND_API_KEY not configured")
        return False

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send(
            {
                "from": from_email or settings.EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        logger.info(f"Email sent successfully to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {subject}. Error: {e}")
        return False


def send_verification_email(to: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"

    subject = "Verify your email address"

    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Welcome to OpenSNS!</h2>
        <p>Please verify your email address to complete your registration.</p>
        <div style="margin: 24px 0;">
            <a href="{verify_url}" 
               style="background: #f59e0b; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; display: inline-block;">
                Verify Email
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            Or copy this link: <a href="{verify_url}">{verify_url}</a>
        </p>
        <p style="color: #666; font-size: 14px;">
            This link expires in 24 hours.
        </p>
        <p style="color: #666; font-size: 14px;">— The OpenSNS Team</p>
    </div>
    """

    return send_email(to, subject, html)


def send_low_credits_warning(
    to: str,
    user_name: str,
    credits_used: int,
    credits_limit: int,
    percentage: int,
) -> bool:
    subject = f"⚠️ You've used {percentage}% of your credits"

    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f59e0b;">Credit Usage Alert</h2>
        <p>Hi {user_name},</p>
        <p>You've used <strong>{percentage}%</strong> of your monthly credits.</p>
        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0;"><strong>{credits_used}</strong> of <strong>{credits_limit}</strong> credits used</p>
        </div>
        <p>To avoid interruption:</p>
        <ul>
            <li><a href="{settings.FRONTEND_URL}/settings/billing">Upgrade your plan</a> for more monthly credits</li>
            <li><a href="{settings.FRONTEND_URL}/settings/billing">Buy a credit pack</a> for immediate top-up</li>
        </ul>
        <p style="color: #666; font-size: 14px;">— The OpenSNS Team</p>
    </div>
    """

    return send_email(to, subject, html)


def send_credits_exhausted(
    to: str,
    user_name: str,
    credits_limit: int,
) -> bool:
    subject = "🛑 You've run out of credits"

    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #ef4444;">Credits Exhausted</h2>
        <p>Hi {user_name},</p>
        <p>You've used all <strong>{credits_limit}</strong> of your monthly credits.</p>
        <p>New generations are paused until you:</p>
        <ul>
            <li><a href="{settings.FRONTEND_URL}/settings/billing">Upgrade your plan</a> for more monthly credits</li>
            <li><a href="{settings.FRONTEND_URL}/settings/billing">Buy a credit pack</a> for immediate top-up</li>
            <li>Wait for your next billing cycle</li>
        </ul>
        <p style="color: #666; font-size: 14px;">— The OpenSNS Team</p>
    </div>
    """

    return send_email(to, subject, html)


def send_autopilot_approval_needed(
    to: str,
    user_name: str,
    rule_product_url: str,
    campaign_id: int,
) -> bool:
    subject = "🤖 Your autopilot campaign is ready for review"
    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #3b82f6;">Autopilot Campaign Ready</h2>
        <p>Hi {user_name},</p>
        <p>Your autopilot schedule just generated new ad creatives for <strong>{rule_product_url}</strong>.</p>
        <div style="background: #eff6ff; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0;">Review and approve them to start using in your campaigns.</p>
        </div>
        <a href="{settings.FRONTEND_URL}/campaigns/{campaign_id}" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none;">Review Campaign</a>
        <p style="color: #666; font-size: 14px; margin-top: 24px;">— The OpenSNS Team</p>
    </div>
    """
    return send_email(to, subject, html)



def send_autopilot_run_failed(
    to: str,
    user_name: str,
    rule_product_url: str,
    error_reason: str,
) -> bool:
    subject = "⚠️ Autopilot run failed"
    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f59e0b;">Autopilot Run Failed</h2>
        <p>Hi {user_name},</p>
        <p>Your autopilot schedule for <strong>{rule_product_url}</strong> encountered an error:</p>
        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0; font-family: monospace; font-size: 13px;">{error_reason}</p>
        </div>
        <p>The schedule will retry on the next scheduled time. If this keeps happening, check your product URL and settings.</p>
        <a href="{settings.FRONTEND_URL}/autopilot" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none;">View Autopilot Settings</a>
        <p style="color: #666; font-size: 14px; margin-top: 24px;">— The OpenSNS Team</p>
    </div>
    """
    return send_email(to, subject, html)



def send_autopilot_credits_insufficient(
    to: str,
    user_name: str,
    rule_product_url: str,
    credits_needed: int,
) -> bool:
    subject = "🛑 Autopilot paused — not enough credits"
    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #ef4444;">Autopilot Paused</h2>
        <p>Hi {user_name},</p>
        <p>Your autopilot schedule for <strong>{rule_product_url}</strong> was skipped because you don't have enough credits ({credits_needed} needed).</p>
        <div style="background: #fef2f2; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0;"><strong>Upgrade to keep your autopilot running without interruption.</strong></p>
        </div>
        <a href="{settings.FRONTEND_URL}/settings/billing" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none;">Upgrade Plan</a>
        <p style="color: #666; font-size: 14px; margin-top: 24px;">— The OpenSNS Team</p>
    </div>
    """
    return send_email(to, subject, html)
