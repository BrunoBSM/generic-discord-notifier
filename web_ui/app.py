"""Flask application factory for Discord Notifier Web UI."""

from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = "discord-notifier-local-only"
    
    # Register routes
    from web_ui.routes import bp
    app.register_blueprint(bp)
    
    return app

