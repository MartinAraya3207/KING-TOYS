import os
import sqlite3
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('ventas', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'kingtoys.db')
SQL_PATH = os.path.join(BASE_DIR, 'database', 'ventas_tablas.sql')

METODOS_PAGO = ('tarjeta', 'efectivo', 'transferencia')
MAX_UNIDADES = 99

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def inicializar_bd():
    """Crea las tablas si no existen (ejecuta el script SQL)."""
    conn = conectar()
    try:
        with open(SQL_PATH, encoding='utf-8') as f:
            conn.executescript(f.read())
    finally:
        conn.close()

@bp.app_template_filter('clp')
def formato_clp(valor):
    """12990 -> $12.990"""
    return f"${int(valor):,}".replace(",", ".")

def leer_carrito(form, productos):
    items = []
    for p in productos:
        bruto = (form.get(f"cant_{p['id_producto']}") or '').strip()
        if bruto in ('', '0'):
            continue
        if not (bruto.isascii() and bruto.isdigit()):
            return None, f'La cantidad de "{p["nombre"]}" no es válida.'
        cantidad = int(bruto)
        if cantidad > MAX_UNIDADES:
            return None, f'Máximo {MAX_UNIDADES} unidades por producto ({p["nombre"]}).'
        if cantidad > p['stock_disponible']:
            return None, f'Stock insuficiente de "{p["nombre"]}" (disponible: {p["stock_disponible"]}).'
        items.append((p, cantidad))
    if not items:
        return None, 'Debes indicar al menos un producto con cantidad mayor a 0.'
    return items, None

def registrar_venta(items, metodo_pago):
    conn = conectar()
    try:
        total = sum(p['precio'] * cant for p, cant in items)
        cur = conn.execute(
            'INSERT INTO venta (fecha, monto_total, metodo_pago, id_vendedor) VALUES (?, ?, ?, ?)',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total, metodo_pago, None)
        )
        id_venta = cur.lastrowid

        for p, cant in items:
            desc = conn.execute(
                'UPDATE producto SET stock_disponible = stock_disponible - ? '
                'WHERE id_producto = ? AND stock_disponible >= ?',
                (cant, p['id_producto'], cant)
            )
            if desc.rowcount != 1:
                raise ValueError(f'Stock insuficiente de "{p["nombre"]}".')

            conn.execute(
                'INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario) '
                'VALUES (?, ?, ?, ?)',
                (id_venta, p['id_producto'], cant, p['precio'])
            )

        conn.commit()
        return id_venta
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@bp.route('/caja', methods=['GET', 'POST'])
def caja():
    conn = conectar()
    productos = conn.execute('SELECT * FROM producto ORDER BY categoria, nombre').fetchall()
    conn.close()

    error = None
    if request.method == 'POST':
        metodo = (request.form.get('metodo_pago') or '').strip().lower()
        if metodo not in METODOS_PAGO:
            error = 'Debes seleccionar un método de pago (tarjeta, efectivo o transferencia).'
        else:
            items, error = leer_carrito(request.form, productos)
            if not error:
                try:
                    id_venta = registrar_venta(items, metodo)
                    return redirect(url_for('ventas.caja', ok=id_venta))
                except ValueError as e:
                    error = str(e)
                except sqlite3.Error:
                    error = 'No se pudo registrar la venta. Intenta nuevamente.'

        conn = conectar()
        productos = conn.execute('SELECT * FROM producto ORDER BY categoria, nombre').fetchall()
        conn.close()

    venta_ok = None
    ok = request.args.get('ok', '')
    if ok.isdigit():
        conn = conectar()
        venta_ok = conn.execute(
            'SELECT id_venta, monto_total, metodo_pago FROM venta WHERE id_venta = ?',
            (int(ok),)
        ).fetchone()
        conn.close()

    return render_template(
        'caja.html',
        productos=productos,
        metodos=METODOS_PAGO,
        error=error,
        venta_ok=venta_ok
    ), (400 if error else 200)

@bp.route('/cuadre')
def cuadre():
    hoy = date.today().isoformat()
    fecha = (request.args.get('fecha') or hoy).strip()
    error = None
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        error, fecha = 'La fecha ingresada no es válida.', hoy

    conn = conectar()
    por_metodo = {m: {'cantidad': 0, 'total': 0} for m in METODOS_PAGO}
    for r in conn.execute(
        'SELECT metodo_pago, COUNT(*) AS n, SUM(monto_total) AS total '
        'FROM venta WHERE date(fecha) = ? GROUP BY metodo_pago',
        (fecha,)
    ):
        por_metodo[r['metodo_pago']] = {'cantidad': r['n'], 'total': r['total']}

    ventas = conn.execute(
        "SELECT v.id_venta, substr(v.fecha, 12, 5) AS hora, v.metodo_pago, v.monto_total, "
        "group_concat(p.nombre || ' x' || d.cantidad, ', ') AS detalle "
        "FROM venta v "
        "JOIN detalle_venta d ON d.id_venta = v.id_venta "
        "JOIN producto p ON p.id_producto = d.id_producto "
        "WHERE date(v.fecha) = ? GROUP BY v.id_venta ORDER BY v.fecha",
        (fecha,)
    ).fetchall()
    conn.close()

    total_dia = sum(x['total'] for x in por_metodo.values())
    n_ventas = sum(x['cantidad'] for x in por_metodo.values())

    return render_template(
        'cuadre.html',
        fecha=fecha,
        hoy=hoy,
        error=error,
        por_metodo=por_metodo,
        ventas=ventas,
        total_dia=total_dia,
        n_ventas=n_ventas
    )