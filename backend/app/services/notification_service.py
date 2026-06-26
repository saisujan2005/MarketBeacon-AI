import os
import logging
import requests
import json
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# Try to import pywebpush for browser push notifications
try:
    from pywebpush import webpush, WebPushException
    _webpush_available = True
except ImportError:
    _webpush_available = False

# HTML Base Email Template (Bloomberg Premium Theme)
EMAIL_TEMPLATE_WRAPPER = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: #0b0f19;
      color: #f3f4f6;
      margin: 0;
      padding: 0;
    }}
    .email-container {{
      max-width: 600px;
      margin: 20px auto;
      background-color: #111827;
      border: 1px solid #1f2937;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    .header {{
      background: linear-gradient(135deg, #1e1b4b, #311042);
      padding: 24px;
      text-align: center;
      border-bottom: 2px solid #00f2fe;
    }}
    .header h1 {{
      margin: 0;
      color: #00f2fe;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .header p {{
      margin: 5px 0 0 0;
      color: #9ca3af;
      font-size: 12px;
      text-transform: uppercase;
    }}
    .content {{
      padding: 24px;
    }}
    .alert-card {{
      background-color: #1f2937;
      border-left: 4px solid #00f2fe;
      padding: 16px;
      border-radius: 4px;
      margin-bottom: 20px;
    }}
    .alert-title {{
      color: #ffffff;
      font-size: 18px;
      font-weight: 600;
      margin-top: 0;
      margin-bottom: 8px;
    }}
    .meta-row {{
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid #374151;
      padding-bottom: 12px;
      margin-bottom: 12px;
    }}
    .meta-item {{
      font-size: 12px;
      color: #9ca3af;
    }}
    .meta-value {{
      font-weight: 600;
      color: #f3f4f6;
    }}
    .summary {{
      font-size: 14px;
      line-height: 1.6;
      color: #d1d5db;
      margin-bottom: 20px;
    }}
    .footer {{
      background-color: #0b0f19;
      padding: 16px;
      text-align: center;
      font-size: 11px;
      color: #6b7280;
      border-top: 1px solid #1f2937;
    }}
    .footer a {{
      color: #00f2fe;
      text-decoration: none;
    }}
    .btn {{
      display: inline-block;
      background: linear-gradient(135deg, #00f2fe, #4facfe);
      color: #0b0f19 !important;
      font-weight: 700;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-size: 14px;
      text-align: center;
      margin-top: 10px;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1>MarketBeacon AI</h1>
      <p>Financial Intelligence Network</p>
    </div>
    <div class="content">
      {body_content}
    </div>
    <div class="footer">
      This is an automated notification from your MarketBeacon AI settings.<br>
      To configure alerts or disable them, go to <a href="{app_url}/settings">Settings</a>.<br>
      © 2026 MarketBeacon AI. All rights reserved.
    </div>
  </div>
</body>
</html>
"""


def is_in_quiet_hours(user_pref) -> bool:
    """
    Checks if current local time (relative to user's timezone) falls inside quiet hours.
    """
    if not user_pref or not user_pref.quiet_hours_enabled:
        return False

    try:
        user_tz = pytz.timezone(user_pref.timezone or "UTC")
        local_time = datetime.now(user_tz)
        current_hour = local_time.hour
        current_minute = local_time.minute

        # Parse start and end times
        start_h, start_m = map(int, user_pref.quiet_hours_start.split(":"))
        end_h, end_m = map(int, user_pref.quiet_hours_end.split(":"))

        current_val = current_hour * 60 + current_minute
        start_val = start_h * 60 + start_m
        end_val = end_h * 60 + end_m

        if start_val < end_val:
            return start_val <= current_val <= end_val
        else:  # Spans midnight
            return current_val >= start_val or current_val <= end_val
    except Exception as e:
        logger.warning(f"Error checking quiet hours: {e}")
        return False


def should_dispatch_email(user_pref, category: str) -> bool:
    """
    Checks if email notifications should be sent to the user based on preferences.
    Categories: 'morning_brief', 'evening_summary', 'smart_alerts', 'watchlist_alerts', 'portfolio_alerts', 'weekly_digest'
    """
    if not user_pref:
        return False

    # Check master email switch
    if not user_pref.email_notifications or not user_pref.notifications_enabled:
        return False

    # Check quiet hours
    if is_in_quiet_hours(user_pref):
        logger.info(f"Notification suppressed due to quiet hours for user preferences ID: {user_pref.id}")
        return False

    # Check category preference
    return getattr(user_pref, category, True)


def should_dispatch_push(user_pref, category: str) -> bool:
    """
    Checks if push notifications should be sent to the user based on preferences.
    """
    if not user_pref:
        return False

    # Check master push switch
    if not user_pref.push_notifications or not user_pref.notifications_enabled:
        return False

    # Check quiet hours
    if is_in_quiet_hours(user_pref):
        logger.info(f"Push notification suppressed due to quiet hours for user preferences ID: {user_pref.id}")
        return False

    # Check category preference
    return getattr(user_pref, category, True)


def send_email_via_resend(api_key: str, to_email: str, subject: str, html_content: str) -> bool:
    """
    Sends an email using Resend REST API.
    """
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "MarketBeacon AI <alerts@marketbeacon.ai>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"Resend: Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Resend error (Status {response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"Resend connection failed: {e}")
        return False


def send_email_via_sendgrid(api_key: str, to_email: str, subject: str, html_content: str) -> bool:
    """
    Sends an email using SendGrid REST API.
    """
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "alerts@marketbeacon.ai", "name": "MarketBeacon AI"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in [200, 201, 202]:
            logger.info(f"SendGrid: Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"SendGrid error (Status {response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"SendGrid connection failed: {e}")
        return False


def dispatch_email(to_email: str, subject: str, body_html: str) -> bool:
    """
    Unified email dispatcher. Dispatches via Resend if available,
    falling back to SendGrid, or printing logs in development.
    """
    app_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    full_html = EMAIL_TEMPLATE_WRAPPER.format(body_content=body_html, app_url=app_url)

    resend_key = os.getenv("RESEND_API_KEY")
    sendgrid_key = os.getenv("SENDGRID_API_KEY")

    if resend_key:
        return send_email_via_resend(resend_key, to_email, subject, full_html)
    elif sendgrid_key:
        return send_email_via_sendgrid(sendgrid_key, to_email, subject, full_html)
    else:
        # Development mode print outbox logs
        logger.info(
            f"\n"
            f"=== DEV EMAIL OUTBOX ===\n"
            f"To: {to_email}\n"
            f"Subject: {subject}\n"
            f"Body Preview: {body_html[:300]}...\n"
            f"========================"
        )
        return True


def dispatch_push(subscription, title: str, body: str, target_url: str = None) -> bool:
    """
    Sends a browser web push notification payload.
    """
    app_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    deep_link = f"{app_url}{target_url}" if target_url else app_url

    payload = {
        "title": title,
        "body": body,
        "url": deep_link
    }

    # Extract VAPID keys from env
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
    claims_email = os.getenv("VAPID_CLAIMS_EMAIL", "alerts@marketbeacon.ai")

    # If VAPID keys are missing or pywebpush is missing, log the event defensively
    if not _webpush_available or not vapid_private_key or not vapid_public_key:
        logger.info(
            f"\n"
            f"=== DEV BROWSER PUSH OUTBOX ===\n"
            f"User Subscription Endpoint: {subscription.endpoint}\n"
            f"Title: {title}\n"
            f"Body: {body}\n"
            f"Deep Link: {deep_link}\n"
            f"==============================="
        )
        return True

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth
        }
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": f"mailto:{claims_email}"},
            timeout=15
        )
        logger.info(f"WebPush: Push notification sent successfully to subscription endpoint: {subscription.endpoint[:50]}...")
        return True
    except WebPushException as ex:
        logger.error(f"WebPush failed: {ex}")
        return False
    except Exception as e:
        logger.error(f"General WebPush error: {e}")
        return False


# ── Notification Event Dispatch Helpers ──────────────────────────────────────────

def dispatch_smart_alert(user, alert) -> None:
    """
    Sends an email and push notification for a Smart Alert.
    """
    user_pref = user.preferences
    app_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    subject = f"🚨 SMART ALERT: {alert.title}"
    body_html = f"""
    <div class="alert-card">
      <h3 class="alert-title">{alert.title}</h3>
      <div class="meta-row">
        <span class="meta-item">Importance Score: <span class="meta-value">{alert.importance_score}/100</span></span>
        <span class="meta-item">Event Type: <span class="meta-value">{alert.event_type}</span></span>
      </div>
      <p class="summary">A high-importance market alert has been triggered for your monitored parameters. Click below to view explanations, impacted assets, and timelines in your terminal.</p>
      <a href="{app_url}/alerts" class="btn">Open Alerts Center</a>
    </div>
    """

    if should_dispatch_email(user_pref, "smart_alerts"):
        dispatch_email(user.email, subject, body_html)


def dispatch_watchlist_alert(user, notification_record) -> None:
    """
    Sends email and push notification when a watchlist keyword overlaps with new alerts.
    """
    user_pref = user.preferences
    app_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    subject = f"⭐ WATCHLIST TRIGGER: '{notification_record.keyword}' in {notification_record.title}"
    body_html = f"""
    <div class="alert-card" style="border-left-color: #10b981;">
      <h3 class="alert-title">{notification_record.title}</h3>
      <div class="meta-row">
        <span class="meta-item">Matched Keyword: <span class="meta-value">{notification_record.keyword}</span></span>
        <span class="meta-item">Sentiment: <span class="meta-value">{notification_record.sentiment or 'NEUTRAL'}</span></span>
      </div>
      <p class="summary">New intelligence matches your watched asset <strong>{notification_record.keyword}</strong>. Click below to investigate full research dossiers and peer comparisons.</p>
      <a href="{app_url}/watchlists" class="btn" style="background: linear-gradient(135deg, #10b981, #059669);">Investigate Watchlist</a>
    </div>
    """

    if should_dispatch_email(user_pref, "watchlist_alerts"):
        dispatch_email(user.email, subject, body_html)
