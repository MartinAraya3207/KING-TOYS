import io
import os
import tempfile
import unittest
from contextlib import closing

import ventas

_module_dir = tempfile.TemporaryDirectory()
ventas.DB_PATH = os.path.join(_module_dir.name, "import.db")
import app as app_module


class ReservasWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        ventas.DB_PATH = os.path.join(self.tempdir.name, "kingtoys.db")
        self.app = app_module.create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
        self.app.instance_path = os.path.join(self.tempdir.name, "instance")
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["vendedor"] = "vendedor-test"
            session["csrf_token"] = "token-test"

    def tearDown(self):
        self.tempdir.cleanup()

    def crear_reserva(self):
        return self.client.post(
            "/reservas",
            data={
                "csrf_token": "token-test",
                "usuario_instagram": "@cliente_prueba",
                "cant_1": "2",
                "comprobante": (io.BytesIO(b"%PDF-1.4 comprobante de prueba"), "comprobante.pdf"),
            },
            content_type="multipart/form-data",
        )

    def buscar_reserva(self):
        with closing(ventas.conectar()) as conn:
            return conn.execute("SELECT * FROM reserva").fetchone()

    def test_aprobar_transferencia_y_completar_retiro(self):
        response = self.crear_reserva()
        self.assertEqual(response.status_code, 302)
        reserva = self.buscar_reserva()
        self.assertEqual(reserva["estado"], "pendiente_validacion")

        with closing(ventas.conectar()) as conn:
            self.assertEqual(
                conn.execute("SELECT stock_disponible FROM producto WHERE id_producto = 1").fetchone()[0],
                10,
            )

        response = self.client.post(
            f"/reservas/{reserva['id_reserva']}/validar",
            data={"csrf_token": "token-test", "accion": "aprobar"},
        )
        self.assertEqual(response.status_code, 302)
        reserva = self.buscar_reserva()
        self.assertEqual(reserva["estado"], "lista_retiro")
        self.assertIsNotNone(reserva["id_venta"])
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(reserva["codigo"], response.get_data(as_text=True))

        response = self.client.get("/retiro-rapido", query_string={"q": "@CLIENTE_PRUEBA"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(reserva["codigo"], response.get_data(as_text=True))

        response = self.client.post(
            f"/retiro-rapido/{reserva['id_reserva']}/completar",
            data={"csrf_token": "token-test"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.buscar_reserva()["estado"], "retirada")

        with closing(ventas.conectar()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM venta").fetchone()[0], 1)

    def test_rechazar_transferencia_libera_stock_y_no_registra_venta(self):
        response = self.crear_reserva()
        self.assertEqual(response.status_code, 302)
        reserva = self.buscar_reserva()
        response = self.client.post(
            f"/reservas/{reserva['id_reserva']}/validar",
            data={"csrf_token": "token-test", "accion": "rechazar"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.buscar_reserva()["estado"], "rechazada")

        with closing(ventas.conectar()) as conn:
            self.assertEqual(
                conn.execute("SELECT stock_disponible FROM producto WHERE id_producto = 1").fetchone()[0],
                12,
            )
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM venta").fetchone()[0], 0)

    def test_no_acepta_comprobante_con_extension_falsa(self):
        response = self.client.post(
            "/reservas",
            data={
                "csrf_token": "token-test",
                "usuario_instagram": "cliente",
                "cant_1": "1",
                "comprobante": (io.BytesIO(b"esto no es un pdf"), "comprobante.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.buscar_reserva())


if __name__ == "__main__":
    unittest.main()
