import os
import re
import secrets
import sqlite3
from datetime import datetime

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename

from ventas import MAX_UNIDADES, conectar

bp = Blueprint("reservas", __name__)

MAX_COMPROBANTE_BYTES = 5 * 1024 * 1024
EXTENSIONES_COMPROBANTE = {
    ".pdf": (b"%PDF-", "application/pdf"),
    ".png": (b"\x89PNG\r\n\x1a\n", "image/png"),
    ".jpg": (b"\xff\xd8\xff", "image/jpeg"),
    ".jpeg": (b"\xff\xd8\xff", "image/jpeg"),
}
ESTADOS_RESERVA = {
    "pendiente_validacion": "Pendiente de validar",
    "lista_retiro": "Lista para retiro",
    "rechazada": "Rechazada",
    "retirada": "Retirada",
}


def normalizar_instagram(valor):
    usuario = (valor or "").strip()
    if usuario.startswith("@"):
        usuario = usuario[1:]
    usuario = usuario.lower()
    if not re.fullmatch(r"[a-z0-9._]{1,30}", usuario, flags=re.ASCII) or not any(
        caracter.isascii() and caracter.isalnum() for caracter in usuario
    ):
        return None
    return usuario


def validar_comprobante(archivo):
    nombre = secure_filename(archivo.filename or "")
    extension = os.path.splitext(nombre)[1].lower()
    tipo = EXTENSIONES_COMPROBANTE.get(extension)
    if not tipo:
        return None, "El comprobante debe ser PDF, PNG o JPG."

    cabecera = archivo.stream.read(16)
    archivo.stream.seek(0)
    if not cabecera.startswith(tipo[0]):
        return None, "El archivo no coincide con el formato declarado."

    archivo.stream.seek(0, os.SEEK_END)
    tamano = archivo.stream.tell()
    archivo.stream.seek(0)
    if tamano <= 0 or tamano > MAX_COMPROBANTE_BYTES:
        return None, "El comprobante debe pesar entre 1 byte y 5 MB."
    return (extension, tipo[1]), None


def guardar_comprobante(archivo, formato):
    extension, _ = formato
    carpeta = os.path.join(current_app.instance_path, "comprobantes_reservas")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{secrets.token_hex(16)}{extension}"
    archivo.save(os.path.join(carpeta, nombre))
    return nombre


def generar_codigo(conn):
    caracteres = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        codigo = "RSV-" + "".join(secrets.choice(caracteres) for _ in range(8))
        if not conn.execute("SELECT 1 FROM reserva WHERE codigo = ?", (codigo,)).fetchone():
            return codigo


def crear_reserva(instagram, archivo_comprobante, formato_comprobante):
    conn = conectar()
    ruta_archivo = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        items = []
        total = 0
        for campo, valor in request.form.items():
            if not campo.startswith("cant_"):
                continue
            cantidad_txt = (valor or "").strip()
            if cantidad_txt in ("", "0"):
                continue
            id_txt = campo.removeprefix("cant_")
            if not id_txt.isascii() or not id_txt.isdigit() or not cantidad_txt.isascii() or not cantidad_txt.isdigit():
                raise ValueError("El producto o la cantidad ingresada no es válida.")
            cantidad = int(cantidad_txt)
            if not 1 <= cantidad <= MAX_UNIDADES:
                raise ValueError(f"Cada cantidad debe estar entre 1 y {MAX_UNIDADES}.")
            producto = conn.execute(
                "SELECT id_producto, nombre, precio FROM producto WHERE id_producto = ?",
                (int(id_txt),),
            ).fetchone()
            if not producto:
                raise ValueError("Uno de los productos seleccionados ya no está disponible.")
            items.append((producto, cantidad))
            total += producto["precio"] * cantidad
        if not items:
            raise ValueError("Selecciona al menos un producto para reservar.")

        codigo = generar_codigo(conn)
        nombre_archivo = guardar_comprobante(archivo_comprobante, formato_comprobante)
        ruta_archivo = os.path.join(current_app.instance_path, "comprobantes_reservas", nombre_archivo)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            "INSERT INTO reserva (codigo, usuario_instagram, fecha, monto_total, comprobante_archivo) "
            "VALUES (?, ?, ?, ?, ?)",
            (codigo, instagram, fecha, total, nombre_archivo),
        )
        id_reserva = cur.lastrowid
        for producto, cantidad in items:
            stock = conn.execute(
                "UPDATE producto SET stock_disponible = stock_disponible - ? "
                "WHERE id_producto = ? AND stock_disponible >= ?",
                (cantidad, producto["id_producto"], cantidad),
            )
            if stock.rowcount != 1:
                raise ValueError(f"Stock insuficiente de «{producto['nombre']}» para esta reserva.")
            conn.execute(
                "INSERT INTO detalle_reserva (id_reserva, id_producto, cantidad, precio_unitario) "
                "VALUES (?, ?, ?, ?)",
                (id_reserva, producto["id_producto"], cantidad, producto["precio"]),
            )
        conn.commit()
        return codigo
    except Exception:
        conn.rollback()
        if ruta_archivo and os.path.isfile(ruta_archivo):
            os.remove(ruta_archivo)
        raise
    finally:
        conn.close()


def cambiar_estado_reserva(id_reserva, accion, vendedor):
    conn = conectar()
    try:
        conn.execute("BEGIN IMMEDIATE")
        reserva = conn.execute(
            "SELECT * FROM reserva WHERE id_reserva = ?", (id_reserva,)
        ).fetchone()
        if not reserva:
            return "not_found"
        if reserva["estado"] != "pendiente_validacion" or accion not in ("aprobar", "rechazar"):
            return "invalid_state"

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if accion == "rechazar":
            detalles = conn.execute(
                "SELECT id_producto, cantidad FROM detalle_reserva WHERE id_reserva = ?",
                (id_reserva,),
            ).fetchall()
            for detalle in detalles:
                conn.execute(
                    "UPDATE producto SET stock_disponible = stock_disponible + ? WHERE id_producto = ?",
                    (detalle["cantidad"], detalle["id_producto"]),
                )
            conn.execute(
                "UPDATE reserva SET estado = 'rechazada', validada_por = ?, fecha_validacion = ? "
                "WHERE id_reserva = ? AND estado = 'pendiente_validacion'",
                (vendedor, fecha, id_reserva),
            )
        else:
            venta = conn.execute(
                "INSERT INTO venta (fecha, monto_total, metodo_pago, id_vendedor) "
                "VALUES (?, ?, 'transferencia', NULL)",
                (fecha, reserva["monto_total"]),
            )
            id_venta = venta.lastrowid
            conn.execute(
                "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario) "
                "SELECT ?, id_producto, cantidad, precio_unitario FROM detalle_reserva WHERE id_reserva = ?",
                (id_venta, id_reserva),
            )
            conn.execute(
                "UPDATE reserva SET estado = 'lista_retiro', validada_por = ?, fecha_validacion = ?, "
                "id_venta = ? WHERE id_reserva = ? AND estado = 'pendiente_validacion'",
                (vendedor, fecha, id_venta, id_reserva),
            )
        conn.commit()
        return "ok"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_reservas():
    conn = conectar()
    try:
        return conn.execute(
            "SELECT r.*, group_concat(p.nombre || ' x' || d.cantidad, ', ') AS productos "
            "FROM reserva r JOIN detalle_reserva d ON d.id_reserva = r.id_reserva "
            "JOIN producto p ON p.id_producto = d.id_producto "
            "GROUP BY r.id_reserva ORDER BY r.id_reserva DESC LIMIT 100"
        ).fetchall()
    finally:
        conn.close()


def reservas_recientes():
    conn = conectar()
    try:
        return conn.execute(
            "SELECT r.codigo, r.usuario_instagram, r.estado, r.monto_total, "
            "group_concat(p.nombre || ' x' || d.cantidad, ', ') AS productos "
            "FROM reserva r JOIN detalle_reserva d ON d.id_reserva = r.id_reserva "
            "JOIN producto p ON p.id_producto = d.id_producto "
            "GROUP BY r.id_reserva ORDER BY r.id_reserva DESC LIMIT 5"
        ).fetchall()
    finally:
        conn.close()


def contar_reservas_pendientes():
    conn = conectar()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM reserva WHERE estado = 'pendiente_validacion'"
        ).fetchone()[0]
    finally:
        conn.close()


@bp.app_template_filter("estado_reserva")
def estado_reserva(estado):
    return ESTADOS_RESERVA.get(estado, estado)


@bp.route("/reservas", methods=["GET", "POST"])
def reservas():
    error = None
    codigo_creado = None
    if request.method == "POST":
        instagram = normalizar_instagram(request.form.get("usuario_instagram"))
        archivo = request.files.get("comprobante")
        if not instagram:
            error = "Ingresa un usuario de Instagram válido, sin espacios."
        elif not archivo or not archivo.filename:
            error = "Adjunta el comprobante de transferencia."
        else:
            formato, error = validar_comprobante(archivo)
            if not error:
                try:
                    codigo_creado = crear_reserva(instagram, archivo, formato)
                except ValueError as exc:
                    error = str(exc)
                except sqlite3.Error:
                    current_app.logger.exception("No se pudo registrar la reserva")
                    error = "No se pudo registrar la reserva. Intenta nuevamente."
                if codigo_creado:
                    return redirect(url_for("reservas.reservas", creada=codigo_creado))

    return render_template(
        "reservas.html",
        productos=obtener_productos(),
        reservas=listar_reservas(),
        error=error,
        creada=request.args.get("creada", ""),
        aviso=request.args.get("aviso", ""),
    ), (400 if error else 200)


def obtener_productos():
    conn = conectar()
    try:
        return conn.execute(
            "SELECT * FROM producto ORDER BY categoria, nombre"
        ).fetchall()
    finally:
        conn.close()


@bp.post("/reservas/<int:id_reserva>/validar")
def validar_transferencia(id_reserva):
    accion = request.form.get("accion", "")
    if accion not in ("aprobar", "rechazar"):
        abort(400)
    try:
        resultado = cambiar_estado_reserva(id_reserva, accion, session.get("vendedor", ""))
    except sqlite3.Error:
        current_app.logger.exception("No se pudo validar la transferencia")
        return redirect(url_for("reservas.reservas", aviso="error"))
    aviso = {
        "ok": "transferencia_aprobada" if accion == "aprobar" else "transferencia_rechazada",
        "not_found": "reserva_no_encontrada",
        "invalid_state": "reserva_ya_procesada",
    }[resultado]
    return redirect(url_for("reservas.reservas", aviso=aviso))

@bp.get("/reservas/<int:id_reserva>/comprobante")
def descargar_comprobante(id_reserva):
    conn = conectar()
    try:
        reserva = conn.execute(
            "SELECT comprobante_archivo FROM reserva WHERE id_reserva = ?",
            (id_reserva,),
        ).fetchone()
    finally:
        conn.close()
    if not reserva:
        abort(404)
    carpeta = os.path.join(current_app.instance_path, "comprobantes_reservas")
    ruta = os.path.join(carpeta, os.path.basename(reserva["comprobante_archivo"]))
    if not os.path.isfile(ruta):
        current_app.logger.error("Falta el comprobante almacenado para la reserva %s", id_reserva)
        abort(404)
    return send_file(ruta, as_attachment=True, download_name="comprobante" + os.path.splitext(ruta)[1])


@bp.route("/retiro-rapido", methods=["GET", "POST"])
def retiro_rapido():
    termino = (request.values.get("q") or "").strip()[:100]
    resultados = []
    error = None
    if termino:
        if termino.upper().startswith("RSV-"):
            consulta = "SELECT * FROM reserva WHERE codigo = ? COLLATE NOCASE"
            parametros = (termino.upper(),)
        else:
            usuario = normalizar_instagram(termino)
            if not usuario:
                error = "Ingresa un código RSV-... o un usuario de Instagram válido."
                usuario = ""
            consulta = "SELECT * FROM reserva WHERE usuario_instagram = ?"
            parametros = (usuario,)
        if not error:
            conn = conectar()
            try:
                filas = conn.execute(
                    f"{consulta} ORDER BY id_reserva DESC LIMIT 50", parametros
                ).fetchall()
                for fila in filas:
                    detalle = conn.execute(
                        "SELECT group_concat(p.nombre || ' x' || d.cantidad, ', ') AS productos "
                        "FROM detalle_reserva d JOIN producto p ON p.id_producto = d.id_producto "
                        "WHERE d.id_reserva = ?",
                        (fila["id_reserva"],),
                    ).fetchone()
                    resultados.append({"reserva": fila, "productos": detalle["productos"]})
            finally:
                conn.close()
    return render_template(
        "retiro_rapido.html",
        termino=termino,
        resultados=resultados,
        error=error,
        aviso=request.args.get("aviso", ""),
    ), (400 if error else 200)


@bp.post("/retiro-rapido/<int:id_reserva>/completar")
def completar_retiro(id_reserva):
    conn = conectar()
    try:
        cur = conn.execute(
            "UPDATE reserva SET estado = 'retirada', fecha_retiro = ? "
            "WHERE id_reserva = ? AND estado = 'lista_retiro'",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_reserva),
        )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        current_app.logger.exception("No se pudo completar el retiro de la reserva")
        return redirect(url_for("reservas.retiro_rapido", aviso="error"))
    finally:
        conn.close()
    aviso = "retiro_completado" if cur.rowcount else "reserva_no_lista"
    return redirect(url_for("reservas.retiro_rapido", aviso=aviso))
