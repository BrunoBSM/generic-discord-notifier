#!/usr/bin/env python3
"""
Discord Notifier - Sends notifications to Discord webhooks based on YAML configuration files.
Designed to be run via cron jobs.
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

import yaml
import requests


def load_config(config_path):
    """Load and parse YAML configuration file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")


def send_discord_webhook(webhook_url, message):
    """Send a message to a Discord webhook."""
    payload = {
        "content": message
    }
    
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
    return response


def send_error_notification(error_webhook_url, error_message):
    """Send an error notification to the error webhook."""
    try:
        payload = {
            "content": f"❌ **Discord Notifier Error**\n\n{error_message}"
        }
        response = requests.post(error_webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        # If error webhook fails, log to stderr
        print(f"CRITICAL: Failed to send error notification: {e}", file=sys.stderr)
        return False


def process_date_placeholders(message):
    """Replace date placeholders in message with current date.
    
    Supported placeholders:
    - {date} - Replaced with current date in DD/MM/YYYY format
    - {date:DD/MM} - Replaced with current date in DD/MM format
    - {date:DD/MM/YYYY} - Replaced with current date in DD/MM/YYYY format
    
    Args:
        message: The message string containing placeholders
        
    Returns:
        The message with placeholders replaced with actual dates
    """
    now = datetime.now()
    
    # Replace {date:DD/MM/YYYY} first (more specific)
    message = message.replace("{date:DD/MM/YYYY}", now.strftime("%d/%m/%Y"))
    
    # Replace {date:DD/MM}
    message = message.replace("{date:DD/MM}", now.strftime("%d/%m"))
    
    # Replace {date} (default to DD/MM/YYYY)
    message = message.replace("{date}", now.strftime("%d/%m/%Y"))
    
    return message


def get_error_webhook_url():
    """Load error webhook URL from error_webhook.yaml file."""
    # Try to find error_webhook.yaml in the same directory as the script
    script_dir = Path(__file__).parent
    error_config_path = script_dir / "error_webhook.yaml"
    
    # Also try in current working directory
    if not error_config_path.exists():
        error_config_path = Path("error_webhook.yaml")
    
    if not error_config_path.exists():
        return None
    
    try:
        config = load_config(error_config_path)
        return config.get("webhook_url")
    except Exception as e:
        print(f"Warning: Could not load error webhook config: {e}", file=sys.stderr)
        return None


def main():
    """Main entry point for the Discord notifier."""
    parser = argparse.ArgumentParser(
        description="Send a Discord notification from a YAML configuration file"
    )
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the YAML configuration file containing webhook_url and message"
    )
    
    args = parser.parse_args()
    config_path = Path(args.config_file)
    
    # Validate config file exists
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    # Load notification configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        error_msg = f"Failed to load configuration file '{config_path}': {e}"
        print(f"Error: {error_msg}", file=sys.stderr)
        
        # Try to send error notification
        error_webhook_url = get_error_webhook_url()
        if error_webhook_url:
            send_error_notification(error_webhook_url, error_msg)
        
        sys.exit(1)
    
    # Validate required fields
    webhook_url = config.get("webhook_url")
    message = config.get("message")
    
    if not webhook_url:
        error_msg = f"Configuration file '{config_path}' missing required field: webhook_url"
        print(f"Error: {error_msg}", file=sys.stderr)
        
        error_webhook_url = get_error_webhook_url()
        if error_webhook_url:
            send_error_notification(error_webhook_url, error_msg)
        
        sys.exit(1)
    
    if not message:
        error_msg = f"Configuration file '{config_path}' missing required field: message"
        print(f"Error: {error_msg}", file=sys.stderr)
        
        error_webhook_url = get_error_webhook_url()
        if error_webhook_url:
            send_error_notification(error_webhook_url, error_msg)
        
        sys.exit(1)
    
    # Process date placeholders in message
    message = process_date_placeholders(message)
    
    # Send notification
    try:
        send_discord_webhook(webhook_url, message)
        sys.exit(0)
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = (
            f"**Failed to send Discord notification**\n"
            f"Config file: `{config_path}`\n"
            f"Time: {timestamp}\n"
            f"Error: {str(e)}"
        )
        print(f"Error: Failed to send notification: {e}", file=sys.stderr)
        
        # Send error notification
        error_webhook_url = get_error_webhook_url()
        if error_webhook_url:
            send_error_notification(error_webhook_url, error_msg)
        else:
            print("Warning: No error webhook configured. Error notification not sent.", file=sys.stderr)
        
        sys.exit(1)
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = (
            f"**Unexpected error in Discord notifier**\n"
            f"Config file: `{config_path}`\n"
            f"Time: {timestamp}\n"
            f"Error: {str(e)}"
        )
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        
        # Send error notification
        error_webhook_url = get_error_webhook_url()
        if error_webhook_url:
            send_error_notification(error_webhook_url, error_msg)
        else:
            print("Warning: No error webhook configured. Error notification not sent.", file=sys.stderr)
        
        sys.exit(1)


if __name__ == "__main__":
    main()

