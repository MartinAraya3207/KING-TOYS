import hmac
import logging
import os
import secrets
from datetime import timedelta

from flask import Flask, abort, redirect, render_template, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash

from ventas import bp as ventas_bp, inicializar_bd


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("KINGTOYS_SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("KINGTOYS_HTTPS", "").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_REFRESH_EACH_REQUEST=True,
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    app.register_blueprint(ventas_bp)
    inicializar_bd()

    @app.context_processor
    def csrf_context():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.before_request
    def require_auth_and_csrf():
        if request.endpoint == "static" or request.endpoint == "login":
            return
        if not session.get("vendedor"):
            return redirect(url_for("login", next=request.path))
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = request.form.get("csrf_token", "")
            if not token or not hmac.compare_digest(token, session.get("csrf_token", "")):
                abort(400)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            token = request.form.get("csrf_token", "")
            if not token or not hmac.compare_digest(token, session.get("csrf_token", "")):
                abort(400)
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            configured_user = os.environ.get("KINGTOYS_USERNAME", "")
            password_hash = os.environ.get("KINGTOYS_PASSWORD_HASH", "")
            valid = bool(configured_user and password_hash and username and password)
            if valid:
                try:
                    valid = hmac.compare_digest(username, configured_user) and check_password_hash(password_hash, password)
                except (ValueError, TypeError):
                    valid = False
            if valid:
                session.clear()
                session.permanent = True
                session["vendedor"] = username
                session["csrf_token"] = secrets.token_urlsafe(32)
                target = request.args.get("next", "")
                if not target.startswith("/") or target.startswith("//"):
                    target = url_for("home")
                return redirect(target)
            app.logger.warning("Intento de inicio de sesión no válido")
            error = "Usuario o contraseña incorrectos."
        return render_template("login.html", error=error)

    @app.route("/", endpoint="home")
    def home():
        return render_template("index.html")

    @app.route('/buscar')
    def buscar():
        termino = (request.args.get('q') or '').strip()[:100]
        return render_template_string('''
        {% extends "base.html" %}{% block content %}<div class="glass-panel" style="text-align:center;padding:50px;">
        <h2>Resultados de búsqueda</h2><p>Buscando en inventario o Instagram: <strong>{{ termino }}</strong></p>
        <a href="/" class="btn-custom btn-outline-custom mt-4">Volver al inicio</a></div>{% endblock %}''', termino=termino)

    @app.route('/retiro-rapido')
    def retiro_rapido():
        return render_template_string(dummy_template, titulo="Retiro Rápido", responsable="Martín", icon="fa-solid fa-bolt")

    @app.route('/reservas')
    def reservas():
        return render_template_string(dummy_template, titulo="Reservas IG", responsable="Martín", icon="fa-brands fa-instagram")

    @app.route('/inventario')
    def inventario():
        return render_template_string(dummy_template, titulo="Inventario", responsable="Ángel y Benjamín", icon="fa-solid fa-boxes-stacked")

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def safe_error(error):
        if getattr(error, "code", None) == 500:
            app.logger.exception("Error interno no controlado")
        code = getattr(error, "code", 500)
        return render_template("error.html", code=code), code

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        return response

    return app


dummy_template = '''
{% extends "base.html" %}{% block content %}<div class="glass-panel"><h2>Módulo: {{ titulo }}</h2>
<p>Pantalla asignada a <strong>{{ responsable }}</strong>.</p><a href="/" class="btn-custom btn-outline-custom mt-4">Volver al Dashboard</a></div>{% endblock %}'''

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, port=5000)
