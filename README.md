# KING-TOYS

Aplicación Flask para ventas, caja y reservas con retiro por Instagram. La base SQLite se crea/actualiza localmente al iniciar; los comprobantes se guardan bajo `instance/comprobantes_reservas/`, fuera de los archivos públicos.

## Ejecutar en Windows (PowerShell)

Desde la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:KINGTOYS_USERNAME = "vendedor"
$env:KINGTOYS_PASSWORD_HASH = (python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Contraseña: ')))")
$env:KINGTOYS_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
python app.py
```

Al pedir `Contraseña:`, escribe la clave para iniciar sesión. Mantén esta misma ventana de PowerShell abierta y visita <http://127.0.0.1:5000>. Las variables de entorno de ejemplo duran mientras esa ventana siga abierta. No publiques el hash, la contraseña, la clave secreta, la base real ni los comprobantes.

Para desarrollo local no definas `KINGTOYS_HTTPS`; detrás de HTTPS en producción establece `KINGTOYS_HTTPS=true` y usa un servidor WSGI de producción. Nunca ejecutes la aplicación de producción con depuración activada.

## Pruebas

Con el entorno virtual activado, ejecuta:

```powershell
python -m unittest discover -s tests -v
```

## Reservas, comprobantes y retiro

1. En **Reservas IG**, ingresa el usuario de Instagram, el/los productos y adjunta un comprobante PDF, PNG o JPG de hasta 5 MB.
2. Se genera un código `RSV-...` y se aparta el stock mientras la reserva queda pendiente.
3. El vendedor descarga/revisa el comprobante y **confirma la transferencia en el banco antes de aprobar**. Aprobar registra la venta como transferencia y habilita el retiro; rechazar libera el stock.
4. En **Retiro Rápido**, busca por código o usuario de Instagram. Entrega solo la reserva con estado “Lista para retiro” y registra la entrega con el botón.

La comprobación del pago es manual: el comprobante por sí solo no confirma que el dinero llegó y esta aplicación no se conecta a bancos. El acceso a las rutas, formularios y comprobantes requiere autenticación y protección CSRF.

## Documentación

Consulte [docs/seguridad-owasp.md](docs/seguridad-owasp.md) para el checklist de seguridad. En esta copia del repositorio no se encontraron los PDF con requisitos; el único documento adicional disponible es `docs/Seguridad_OWASP_KING-TOYS.docx`. La implementación de RF-01/RF-02 sigue la descripción proporcionada y deberá contrastarse con esos PDF cuando estén disponibles.
