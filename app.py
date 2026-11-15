from flask import Flask, render_template, request, render_template_string
from ventas import bp as ventas_bp, inicializar_bd  # Módulo de Benjamín

app = Flask(__name__)
app.register_blueprint(ventas_bp)
inicializar_bd()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buscar')
def buscar():
    termino = request.args.get('q')
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="glass-panel" style="text-align: center; padding: 50px;">
        <h2 style='color:var(--text-main); font-family: "Orbitron", sans-serif; margin-top: 20px;'>
            <i class="fa-solid fa-magnifying-glass" style="color: var(--kt-yellow);"></i> Resultados de búsqueda
        </h2>
        <p style='color:var(--text-muted); font-size: 1.1rem; margin-top: 20px;'>Buscando en inventario o Instagram: <strong style="color: #fff;">{{ termino }}</strong></p>
        <a href='/' class='btn-custom btn-outline-custom mt-4'>Volver al inicio</a>
    </div>
    {% endblock %}
    ''', termino=termino)

dummy_template = '''
{% extends "base.html" %}
{% block content %}
<div class="glass-panel" style="min-height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
    <i class="{{ icon }}" style="font-size: 4rem; color: var(--kt-red); margin-bottom: 20px; text-shadow: 0 0 20px rgba(230,36,41,0.4);"></i>
    <h2 style='color:var(--text-main); font-family: "Orbitron", sans-serif;'>Módulo: {{ titulo }}</h2>
    <p style='color:var(--text-muted); max-width: 500px; margin-top: 15px;'>
        Esta es la pantalla asignada a <strong>{{ responsable }}</strong>.<br>
        Aquí debe conectar su código Python y base de datos. El diseño base (layout) ya está funcionando.
    </p>
    <a href='/' class='btn-custom btn-outline-custom mt-4'>Volver al Dashboard</a>
</div>
{% endblock %}
'''

@app.route('/retiro-rapido')
def retiro_rapido():
    return render_template_string(dummy_template, titulo="Retiro Rápido", responsable="Martín", icon="fa-solid fa-bolt")

@app.route('/reservas')
def reservas():
    return render_template_string(dummy_template, titulo="Reservas IG", responsable="Martín", icon="fa-brands fa-instagram")

@app.route('/inventario')
def inventario():
    return render_template_string(dummy_template, titulo="Inventario", responsable="Ángel y Benjamín", icon="fa-solid fa-boxes-stacked")

@app.route('/logout')
def logout():
    return render_template_string(dummy_template, titulo="Cierre de Sesión Seguro", responsable="Maximiliano (OWASP)", icon="fa-solid fa-arrow-right-from-bracket")

if __name__ == '__main__':
    app.run(debug=True, port=5000)