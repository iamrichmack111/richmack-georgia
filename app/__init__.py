import os
from flask import Flask
from .db import init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'local-dev-only-change-me'),
        DATABASE=os.getenv('DATABASE', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'georgia.db')),
    )
    if test_config:
        app.config.update(test_config)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        init_db()

    return app
