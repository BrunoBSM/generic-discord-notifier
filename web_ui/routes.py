"""Flask routes for Discord Notifier Web UI."""

import re
from datetime import datetime

import requests
from flask import Blueprint, flash, redirect, render_template, request, url_for

from web_ui.config_manager import ConfigManager
from web_ui.cron_manager import CronManager

bp = Blueprint("main", __name__)

# Initialize managers
config_manager = ConfigManager()
cron_manager = CronManager()


def process_date_placeholders(message: str) -> str:
    """Preview date placeholders with current date."""
    now = datetime.now()
    message = message.replace("{date:DD/MM/YYYY}", now.strftime("%d/%m/%Y"))
    message = message.replace("{date:DD/MM}", now.strftime("%d/%m"))
    message = message.replace("{date}", now.strftime("%d/%m/%Y"))
    return message


@bp.route("/")
def dashboard():
    """Main dashboard showing all notifications."""
    configs = config_manager.list_configs()
    cron_jobs = cron_manager.get_all_notification_jobs()
    
    # Merge config and cron info
    notifications = []
    for cfg in configs:
        name = cfg["name"]
        job_info = cron_jobs.get(name)
        
        notifications.append({
            "name": name,
            "webhook_url": cfg["webhook_url"],
            "message": cfg["message"],
            "message_preview": (cfg["message"][:80] + "...") if len(cfg["message"]) > 80 else cfg["message"],
            "enabled": job_info.enabled if job_info else False,
            "schedule": job_info.schedule if job_info else None,
            "schedule_human": job_info.schedule_human if job_info else None,
            "next_run": job_info.next_run if job_info else None,
        })
    
    return render_template("dashboard.html", notifications=notifications)


@bp.route("/notification/new", methods=["GET", "POST"])
def new_notification():
    """Create a new notification."""
    presets = cron_manager.get_schedule_presets()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        webhook_url = request.form.get("webhook_url", "").strip()
        message = request.form.get("message", "").strip()
        
        # Validate name
        if not name:
            flash("Name is required.", "error")
            return render_template("edit.html", is_new=True, presets=presets,
                                   name=name, webhook_url=webhook_url, message=message)
        
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            flash("Name can only contain letters, numbers, dashes, and underscores.", "error")
            return render_template("edit.html", is_new=True, presets=presets,
                                   name=name, webhook_url=webhook_url, message=message)
        
        if config_manager.config_exists(name):
            flash(f"A notification named '{name}' already exists.", "error")
            return render_template("edit.html", is_new=True, presets=presets,
                                   name=name, webhook_url=webhook_url, message=message)
        
        if not webhook_url:
            flash("Webhook URL is required.", "error")
            return render_template("edit.html", is_new=True, presets=presets,
                                   name=name, webhook_url=webhook_url, message=message)
        
        if not message:
            flash("Message is required.", "error")
            return render_template("edit.html", is_new=True, presets=presets,
                                   name=name, webhook_url=webhook_url, message=message)
        
        # Save config
        if config_manager.save_config(name, webhook_url, message):
            flash(f"Notification '{name}' created successfully!", "success")
            return redirect(url_for("main.edit_notification", name=name))
        else:
            flash("Failed to save configuration.", "error")
    
    return render_template("edit.html", is_new=True, presets=presets,
                           name="", webhook_url="", message="")


@bp.route("/notification/<name>", methods=["GET", "POST"])
def edit_notification(name: str):
    """Edit an existing notification."""
    config = config_manager.load_config(name)
    
    if not config:
        flash(f"Notification '{name}' not found.", "error")
        return redirect(url_for("main.dashboard"))
    
    job_info = cron_manager.get_job_status(name)
    presets = cron_manager.get_schedule_presets()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "save":
            webhook_url = request.form.get("webhook_url", "").strip()
            message = request.form.get("message", "").strip()
            
            if not webhook_url:
                flash("Webhook URL is required.", "error")
            elif not message:
                flash("Message is required.", "error")
            elif config_manager.save_config(name, webhook_url, message):
                flash("Configuration saved!", "success")
                config = config_manager.load_config(name)
            else:
                flash("Failed to save configuration.", "error")
        
        elif action == "enable":
            schedule = request.form.get("schedule", "0 9 * * *")
            if schedule == "custom":
                schedule = request.form.get("custom_schedule", "0 9 * * *")
            command = config_manager.get_notifier_command(name)
            
            if cron_manager.enable_notification(name, command, schedule):
                flash(f"Notification enabled with schedule: {cron_manager._schedule_to_human(schedule)}", "success")
                job_info = cron_manager.get_job_status(name)
            else:
                flash("Failed to enable notification.", "error")
        
        elif action == "disable":
            if cron_manager.disable_notification(name):
                flash("Notification disabled.", "success")
                job_info = cron_manager.get_job_status(name)
            else:
                flash("Failed to disable notification.", "error")
        
        elif action == "update_schedule":
            schedule = request.form.get("schedule", "0 9 * * *")
            if schedule == "custom":
                schedule = request.form.get("custom_schedule", "0 9 * * *")
            command = config_manager.get_notifier_command(name)
            
            if cron_manager.enable_notification(name, command, schedule):
                flash(f"Schedule updated: {cron_manager._schedule_to_human(schedule)}", "success")
                job_info = cron_manager.get_job_status(name)
            else:
                flash("Failed to update schedule.", "error")
    
    return render_template(
        "edit.html",
        is_new=False,
        name=name,
        webhook_url=config.get("webhook_url", ""),
        message=config.get("message", ""),
        message_preview=process_date_placeholders(config.get("message", "")),
        enabled=job_info.enabled,
        schedule=job_info.schedule or "0 9 * * *",
        schedule_human=job_info.schedule_human,
        next_run=job_info.next_run,
        presets=presets,
    )


@bp.route("/notification/<name>/test", methods=["POST"])
def test_notification(name: str):
    """Send a test notification."""
    config = config_manager.load_config(name)
    
    if not config:
        flash(f"Notification '{name}' not found.", "error")
        return redirect(url_for("main.dashboard"))
    
    webhook_url = config.get("webhook_url")
    message = config.get("message", "")
    
    if not webhook_url:
        flash("No webhook URL configured.", "error")
        return redirect(url_for("main.edit_notification", name=name))
    
    # Process date placeholders
    message = process_date_placeholders(message)
    
    # Add test indicator
    test_message = f"🧪 **TEST NOTIFICATION**\n\n{message}"
    
    try:
        response = requests.post(
            webhook_url,
            json={"content": test_message},
            timeout=10
        )
        response.raise_for_status()
        flash("Test notification sent successfully!", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Failed to send test notification: {e}", "error")
    
    return redirect(url_for("main.edit_notification", name=name))


@bp.route("/notification/<name>/delete", methods=["POST"])
def delete_notification(name: str):
    """Delete a notification."""
    # First disable the cron job
    cron_manager.disable_notification(name)
    
    # Then delete the config
    if config_manager.delete_config(name):
        flash(f"Notification '{name}' deleted.", "success")
    else:
        flash(f"Failed to delete notification '{name}'.", "error")
    
    return redirect(url_for("main.dashboard"))


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    """Error webhook settings."""
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "save":
            webhook_url = request.form.get("webhook_url", "").strip()
            
            if config_manager.save_error_webhook(webhook_url):
                flash("Error webhook saved!", "success")
            else:
                flash("Failed to save error webhook.", "error")
        
        elif action == "test":
            webhook_url = config_manager.load_error_webhook()
            
            if not webhook_url:
                flash("No error webhook configured.", "error")
            else:
                try:
                    test_message = "🧪 **TEST ERROR WEBHOOK**\n\nThis is a test of the error notification system."
                    response = requests.post(
                        webhook_url,
                        json={"content": test_message},
                        timeout=10
                    )
                    response.raise_for_status()
                    flash("Test error notification sent!", "success")
                except requests.exceptions.RequestException as e:
                    flash(f"Failed to send test: {e}", "error")
    
    error_webhook = config_manager.load_error_webhook() or ""
    
    return render_template("settings.html", error_webhook=error_webhook)

