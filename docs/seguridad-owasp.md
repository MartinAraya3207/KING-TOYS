# Seguridad OWASP y revisión de módulos

**Proyecto:** KING-TOYS · **Responsable:** Maximiliano · **Fecha:** 19 de noviembre de 2026

## Medidas implementadas

- **Control de acceso (OWASP A01):** todas las rutas de la aplicación, incluidas caja, cuadre, búsqueda, dashboard, inventario, reservas y retiro rápido, pasan por autenticación. La ruta pública de inicio de sesión es la única excepción de aplicación. La ruta de cierre de sesión solo acepta POST.
- **Autenticación y sesiones:** contraseña verificada con `werkzeug.security.check_password_hash` (hash PBKDF2 generado por Werkzeug); usuario, hash y secreto se reciben del entorno. No hay claves por defecto. Sesión permanente con expiración de 30 minutos, renovación durante actividad y cookie HttpOnly, SameSite=Lax; Secure se activa para HTTPS.
- **Protección CSRF:** token aleatorio por sesión, comparado en tiempo constante, obligatorio en todos los formularios POST/PUT/PATCH/DELETE, incluido login, ventas y cierre de sesión.
- **Inyección (OWASP A03):** las consultas de ventas usan placeholders SQLite (`?`) y parámetros separados. La fecha y el ID del recibo también se enlazan como parámetros. No concatenar valores del usuario dentro del SQL.
- **Validación:** cantidad de productos requiere dígitos ASCII, está limitada a 99 y se valida contra stock disponible; método de pago usa una lista permitida; fecha se analiza como `YYYY-MM-DD`; búsqueda se recorta a 100 caracteres. La base agrega restricciones CHECK, claves foráneas y unicidad.
- **XSS:** las vistas usan autoescape de Jinja; valores de búsqueda y ventas se renderizan como texto. No usar `safe` para datos de usuario.
- **Errores e información sensible:** el usuario recibe mensajes genéricos y no recibe trazas ni detalles SQL; los errores internos se registran en el servidor. No activar `debug` en despliegue.
- **Cabeceras:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y Content-Security-Policy.
- **Secretos y datos:** `.gitignore` excluye `.env`, bases SQLite y archivos de entorno virtual. No se agregaron credenciales de vendedor al repositorio.

## Revisión de los módulos disponibles

| Área | Resultado de revisión |
| --- | --- |
| `app.py` y rutas de pantalla | Autenticación global; mensajes Jinja autoescapados; búsqueda acotada; errores controlados. |
| Ventas y cuadre (`ventas.py`) | SQL parametrizado en lectura, registro, actualización de stock y cuadre. Validación del carrito y del método de pago en servidor. El stock se actualiza con condición atómica y la venta usa transacción con rollback. |
| Formularios (`templates/`) | Login, venta y logout incluyen token CSRF; Jinja escapa valores. |
| Inventario, retiro y reservas | En esta copia solo son pantallas temporales de demostración; no hay consultas ni formularios de negocio que revisar. |

## Checklist de despliegue

- [ ] Definir `KINGTOYS_USERNAME`, `KINGTOYS_PASSWORD_HASH` y `KINGTOYS_SECRET_KEY` fuera del repositorio.
- [ ] Publicar exclusivamente detrás de HTTPS y activar `KINGTOYS_HTTPS=true`.
- [ ] Mantener Flask en versión soportada y actualizar dependencias según el entorno final.
- [ ] Rotar secreto y contraseña si se exponen; excluir y respaldar de forma segura la base real.
- [ ] Reunir las referencias aportadas por los demás integrantes: esta copia no contiene bibliografía ni código de sus módulos.

La CSP permite estilos y scripts inline porque las plantillas existentes contienen CSS y JavaScript inline. Para endurecerla, trasladar esos bloques a archivos estáticos y retirar `'unsafe-inline'`.

## Bibliografía (APA 7.ª edición)

Flask. (s. f.). *Web security*. Pallets Projects. https://flask.palletsprojects.com/en/stable/web-security/

OWASP Foundation. (2021). *A01:2021 – Broken access control*. OWASP Top 10. https://owasp.org/Top10/A01_2021-Broken_Access_Control/

OWASP Foundation. (2021). *A03:2021 – Injection*. OWASP Top 10. https://owasp.org/Top10/A03_2021-Injection/

OWASP Foundation. (s. f.). *Cross-site request forgery prevention cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

OWASP Foundation. (s. f.). *Password storage cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

OWASP Foundation. (s. f.). *SQL injection prevention cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

Pallets. (s. f.). *Werkzeug security helpers*. https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
