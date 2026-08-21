"""
SMTP Email Notification Service
Healthcare Data Quality & Anomaly Operations Platform

Supports:
- Worker account invitation & credential setup
- Critical data quality anomaly alerts (Isolation Forest & Rule Engine)
- SLA risk and SLA breach warnings
- Worker task assignment alerts
- Admin notification preferences & live SMTP test dispatch
"""

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional, Tuple

from app.config import settings

logger = logging.getLogger("email_service")

# Path to persisted notification settings
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "notification_settings.json")


def _get_default_settings() -> Dict[str, Any]:
    return {
        "email_notifications_enabled": True,
        "worker_invitations": True,
        "critical_anomalies": True,
        "sla_at_risk": True,
        "sla_breached": True,
        "pipeline_failures": True,
        "worker_assignments": True,
        "smtp_host": settings.SMTP_HOST or "smtp.gmail.com",
        "smtp_port": settings.SMTP_PORT or 587,
        "smtp_username": settings.SMTP_USERNAME or "",
        "smtp_password": settings.SMTP_PASSWORD or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or "notifications@healthdata-ops.internal",
        "smtp_from_name": settings.SMTP_FROM_NAME or "Healthcare DQ Monitor",
        "smtp_use_tls": settings.SMTP_USE_TLS,
        "admin_alert_email": "admin@healthdata-ops.internal",
    }


def load_notification_settings() -> Dict[str, Any]:
    default = _get_default_settings()
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default.update(saved)
    except Exception as exc:
        logger.warning(f"Could not load notification settings from disk: {exc}")
    return default


def save_notification_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
    current = load_notification_settings()
    current.update(new_settings)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as exc:
        logger.warning(f"Could not save notification settings to disk: {exc}")
    return current


def send_smtp_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    custom_cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Sends an email via SMTP.
    Falls back gracefully to logging in development if SMTP credentials are not yet configured.
    """
    cfg = custom_cfg or load_notification_settings()

    if not cfg.get("email_notifications_enabled", True):
        return False, "Email notifications are globally disabled in Notification Settings."

    host = cfg.get("smtp_host", "smtp.gmail.com").strip()
    port = int(cfg.get("smtp_port", 587))
    username = str(cfg.get("smtp_username", "")).strip()
    password = str(cfg.get("smtp_password", "")).strip()

    # Automatically clean spaces in Gmail 16-character App Passwords
    if "gmail" in host.lower() and len(password.replace(" ", "")) == 16:
        password = password.replace(" ", "")

    from_email = cfg.get("smtp_from_email", username or "notifications@healthdata-ops.internal").strip()
    from_name = cfg.get("smtp_from_name", "Healthcare DQ Monitor").strip()
    use_tls = cfg.get("smtp_use_tls", True)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    # In development without active SMTP credentials, log formatted message and succeed smoothly
    if not username or not password:
        log_msg = f"[SMTP DEV SIMULATOR] Email dispatched to {to_email} | Subject: {subject}"
        print(log_msg)
        logger.info(log_msg)
        return True, "Email generated and dispatched (Dev SMTP simulator active: set SMTP_USERNAME & SMTP_PASSWORD for live relay)."

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()

        server.login(username, password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Successfully sent live SMTP email to {to_email}")
        return True, f"Live email successfully delivered to {to_email} via {host}:{port}"
    except Exception as exc:
        err_msg = f"SMTP Relay error sending to {to_email}: {str(exc)}"
        logger.error(err_msg)
        return False, err_msg



# ── HTML Template Builders ──────────────────────────────────────────────────

def _wrap_email_template(title: str, preheader: str, body_html: str) -> str:
    """Wraps body in an executive healthcare dark/blue email layout."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px 30px; text-align: left; border-bottom: 2px solid #2563eb; }}
    .header-logo {{ color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: -0.5px; margin: 0; }}
    .header-sub {{ color: #94a3b8; font-size: 12px; margin: 4px 0 0 0; text-transform: uppercase; letter-spacing: 1px; }}
    .content {{ padding: 30px; color: #334155; font-size: 14px; line-height: 1.6; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; font-family: monospace; }}
    .badge-critical {{ background-color: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }}
    .badge-warning {{ background-color: #fef3c7; color: #d97706; border: 1px solid #fde68a; }}
    .badge-info {{ background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }}
    .card {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 18px 0; }}
    .btn {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; text-align: center; margin: 15px 0; }}
    .btn-emerald {{ background-color: #059669; }}
    .footer {{ background-color: #f8fafc; padding: 20px 30px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #64748b; line-height: 1.5; }}
    .kv-row {{ display: table; width: 100%; margin-bottom: 6px; }}
    .kv-key {{ display: table-cell; width: 35%; font-weight: 600; color: #64748b; font-size: 12px; }}
    .kv-val {{ display: table-cell; width: 65%; font-weight: 600; color: #0f172a; font-family: monospace; font-size: 12px; }}
  </style>
</head>
<body>
  <div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">
    {preheader}
  </div>
  <div class="container">
    <div class="header">
      <h1 class="header-logo">Healthcare Data Quality Monitor</h1>
      <p class="header-sub">Automated Claim & Prior-Auth Operations</p>
    </div>
    <div class="content">
      {body_html}
    </div>
    <div class="footer">
      <p>This is an automated operational notification sent by the Healthcare Data Quality & Anomaly Operations Platform.<br>
      HIPAA & Regulatory Compliance: Ingestion logs and audit trails are immutable.</p>
    </div>
  </div>
</body>
</html>"""


# ── Specialized Notification Dispatches ─────────────────────────────────────

def send_worker_invitation(worker_email: str, worker_name: str, invite_token: Optional[str] = None) -> Tuple[bool, str]:
    """Dispatches onboarding invitation with account credential setup link."""
    cfg = load_notification_settings()
    if not cfg.get("worker_invitations", True):
        return False, "Worker invitation notifications are disabled."

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    setup_link = f"{frontend_url}/set-password?token={invite_token}" if invite_token else f"{frontend_url}/login"

    subject = "Welcome to Healthcare DQ Operations — Activate Your Operator Account"
    preheader = f"Welcome {worker_name}! Activate your operator account to begin reviewing claims data quality."

    body = f"""
      <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">Welcome to the Data Operations Team, {worker_name}</h2>
      <p>An administrator has registered your profile as an authorized <strong>Claims & Prior-Authorization Data Steward</strong>.</p>
      
      <div class="card">
        <div class="kv-row"><div class="kv-key">Operator Name:</div><div class="kv-val">{worker_name}</div></div>
        <div class="kv-row"><div class="kv-key">Login Email:</div><div class="kv-val">{worker_email}</div></div>
        <div class="kv-row"><div class="kv-key">Assigned Domain:</div><div class="kv-val">Claims & Prior-Authorizations</div></div>
        <div class="kv-row"><div class="kv-key">Access Role:</div><div class="kv-val">Data Quality Reviewer / Worker</div></div>
      </div>

      <p>Please click the button below to set up your password and access the real-time anomaly review dashboard:</p>
      <div style="text-align: center;">
        <a href="{setup_link}" class="btn">Activate Your Operator Account</a>
      </div>
      <p style="font-size: 12px; color: #64748b;">Direct link: <a href="{setup_link}" style="color: #2563eb;">{setup_link}</a></p>
    """

    html = _wrap_email_template("Operator Account Invitation", preheader, body)
    return send_smtp_email(worker_email, subject, html)


def send_critical_anomaly_alert(recipient_email: str, anomaly_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Dispatches high-urgency alert when a Critical anomaly is identified."""
    cfg = load_notification_settings()
    if not cfg.get("critical_anomalies", True):
        return False, "Critical anomaly notifications are disabled."

    record_id = anomaly_data.get("record_id", "N/A")
    anomaly_type = anomaly_data.get("anomaly_type", "Data Quality Anomaly")
    source = anomaly_data.get("source_dataset", "CLAIMS")
    affected_field = anomaly_data.get("affected_field", "General Record")
    error_msg = anomaly_data.get("error_message", "Outlier detected by ML inference pipeline")
    likely_cause = anomaly_data.get("likely_cause", "Input format discrepancy or upstream service issue")
    recommended_fix = anomaly_data.get("recommended_fix", "Inspect source payload and apply data standard normalization")
    
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    investigate_url = f"{frontend_url}/anomalies"

    subject = f"🔴 Critical Data Quality Alert: [{source}] Record {record_id}"
    preheader = f"Critical anomaly detected on pipeline {source}. Immediate steward review required."

    body = f"""
      <div style="margin-bottom: 12px;">
        <span class="badge badge-critical">CRITICAL SEVERITY</span>
        <span class="badge badge-info" style="margin-left: 6px;">{source}</span>
      </div>
      <h2 style="color: #991b1b; margin-top: 0; font-size: 18px;">Critical Data Quality Anomaly Detected</h2>
      <p>The automated ML scoring and rule engine flagged an urgent data quality incident requiring immediate human review:</p>
      
      <div class="card">
        <div class="kv-row"><div class="kv-key">Record ID:</div><div class="kv-val">{record_id}</div></div>
        <div class="kv-row"><div class="kv-key">Source Feed:</div><div class="kv-val">{source}</div></div>
        <div class="kv-row"><div class="kv-key">Anomaly Type:</div><div class="kv-val">{anomaly_type}</div></div>
        <div class="kv-row"><div class="kv-key">Affected Field:</div><div class="kv-val">{affected_field}</div></div>
        <div class="kv-row"><div class="kv-key">Issue Summary:</div><div class="kv-val" style="color: #b91c1c;">{error_msg}</div></div>
      </div>

      <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; margin: 16px 0; border-radius: 4px;">
        <strong style="color: #92400e; font-size: 12px; text-transform: uppercase;">Attributed Likely Cause:</strong>
        <p style="margin: 4px 0 0 0; font-size: 13px; color: #78350f;">{likely_cause}</p>
      </div>

      <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 12px; margin: 16px 0; border-radius: 4px;">
        <strong style="color: #065f46; font-size: 12px; text-transform: uppercase;">RAG Recommended Remediation:</strong>
        <p style="margin: 4px 0 0 0; font-size: 13px; color: #047857;">{recommended_fix}</p>
      </div>

      <div style="text-align: center; margin-top: 20px;">
        <a href="{investigate_url}" class="btn">Investigate Anomaly in Dashboard</a>
      </div>
    """

    html = _wrap_email_template("Critical Anomaly Alert", preheader, body)
    return send_smtp_email(recipient_email, subject, html)


def send_sla_breach_alert(
    recipient_email: str,
    pipeline_name: str,
    record_id: str,
    elapsed_hours: float,
    target_hours: int,
    is_breach: bool = True,
) -> Tuple[bool, str]:
    """Dispatches SLA risk or SLA breach alert to assigned steward and admin."""
    cfg = load_notification_settings()
    if is_breach and not cfg.get("sla_breached", True):
        return False, "SLA breach alerts disabled."
    if not is_breach and not cfg.get("sla_at_risk", True):
        return False, "SLA risk alerts disabled."

    status_title = "🔴 SLA Breached" if is_breach else "⚠️ SLA At Immediate Risk"
    badge_class = "badge-critical" if is_breach else "badge-warning"
    subject = f"{status_title}: [{pipeline_name}] Record {record_id}"
    preheader = f"Operational SLA alert for pipeline {pipeline_name}. Target: {target_hours}h, Elapsed: {elapsed_hours:.1f}h."

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    sla_url = f"{frontend_url}/sla"

    body = f"""
      <div style="margin-bottom: 12px;">
        <span class="badge {badge_class}">{"SLA BREACHED" if is_breach else "SLA AT RISK"}</span>
      </div>
      <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">{status_title}</h2>
      <p>An unresolved claims anomaly record has exceeded or is nearing the operational SLA turnaround threshold:</p>
      
      <div class="card">
        <div class="kv-row"><div class="kv-key">Pipeline / Feed:</div><div class="kv-val">{pipeline_name}</div></div>
        <div class="kv-row"><div class="kv-key">Record ID:</div><div class="kv-val">{record_id}</div></div>
        <div class="kv-row"><div class="kv-key">Target SLA:</div><div class="kv-val">{target_hours}.0 Hours</div></div>
        <div class="kv-row"><div class="kv-key">Elapsed Processing:</div><div class="kv-val" style="color: #dc2626;">{elapsed_hours:.1f} Hours</div></div>
      </div>

      <p>Immediate steward action is required to resolve or escalate the record before downstream claims adjudication delays occur.</p>
      <div style="text-align: center;">
        <a href="{sla_url}" class="btn">View SLA Queue & Extend Target</a>
      </div>
    """

    html = _wrap_email_template(status_title, preheader, body)
    return send_smtp_email(recipient_email, subject, html)


def send_assignment_notification(
    worker_email: str,
    worker_name: str,
    anomaly_data: Dict[str, Any],
    assigned_by: str = "Admin",
) -> Tuple[bool, str]:
    """Dispatches assignment notification when an admin assigns an anomaly to a worker."""
    cfg = load_notification_settings()
    if not cfg.get("worker_assignments", True):
        return False, "Worker assignment alerts disabled."

    record_id = anomaly_data.get("record_id", "N/A")
    anomaly_type = anomaly_data.get("anomaly_type", "Data Quality Review")
    source = anomaly_data.get("source_dataset", "CLAIMS")
    severity = str(anomaly_data.get("severity", "MEDIUM")).upper()

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    review_url = f"{frontend_url}/review"

    subject = f"📋 New Task Assigned: [{source}] Record {record_id}"
    preheader = f"Hello {worker_name}, you have been assigned an anomaly record for review by {assigned_by}."

    body = f"""
      <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">New Anomaly Assigned to You</h2>
      <p>Hello {worker_name}, administrator <strong>{assigned_by}</strong> has assigned a data quality anomaly for your review and resolution:</p>
      
      <div class="card">
        <div class="kv-row"><div class="kv-key">Record ID:</div><div class="kv-val">{record_id}</div></div>
        <div class="kv-row"><div class="kv-key">Source Dataset:</div><div class="kv-val">{source}</div></div>
        <div class="kv-row"><div class="kv-key">Anomaly Category:</div><div class="kv-val">{anomaly_type}</div></div>
        <div class="kv-row"><div class="kv-key">Assigned Severity:</div><div class="kv-val">{severity}</div></div>
      </div>

      <div style="text-align: center;">
        <a href="{review_url}" class="btn">Open Review Workspace</a>
      </div>
    """

    html = _wrap_email_template("Task Assignment Notification", preheader, body)
    return send_smtp_email(worker_email, subject, html)


def send_test_email(recipient_email: str, test_cfg: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """Verifies live SMTP connection and credentials by sending a test message."""
    subject = "✅ SMTP Configuration Test — Healthcare DQ Platform"
    preheader = "Your SMTP notification settings are configured and verified successfully."
    body = f"""
      <div style="margin-bottom: 12px;">
        <span class="badge badge-info">VERIFICATION SUCCESSFUL</span>
      </div>
      <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">SMTP Relay Connection Verified</h2>
      <p>This email confirms that your SMTP server settings, credentials, and notification pipelines are operating properly.</p>
      
      <div class="card">
        <div class="kv-row"><div class="kv-key">Test Recipient:</div><div class="kv-val">{recipient_email}</div></div>
        <div class="kv-row"><div class="kv-key">Service:</div><div class="kv-val">Healthcare Data Operations Platform</div></div>
        <div class="kv-row"><div class="kv-key">Status:</div><div class="kv-val" style="color: #059669;">Ready for Live Alerts</div></div>
      </div>
    """
    html = _wrap_email_template("SMTP Test Email", preheader, body)
    return send_smtp_email(recipient_email, subject, html, custom_cfg=test_cfg)
