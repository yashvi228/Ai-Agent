from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import AppConfig
from .middleware import init_logging


limiter: Limiter | None = None


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(AppConfig())

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}}
    )

    init_logging(app)

    global limiter
    limiter = Limiter(get_remote_address, app=app, default_limits=["60/minute", "600/hour"])  # type: ignore

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    from .routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from flask import render_template

    @app.get("/")
    def index():
        return render_template("index.html")

    return app

