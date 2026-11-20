# KING-TOYS

Aplicación Flask para ventas y caja. La autenticación de vendedor debe configurarse antes de iniciar el servidor.

## Configuración segura

Use variables de entorno, nunca incluya credenciales en el repositorio. Cree un hash de contraseña con Werkzeug:

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Contraseña: ')))"
$env:KINGTOYS_USERNAME = "vendedor"
$env:KINGTOYS_PASSWORD_HASH = "<hash generado>"
$env:KINGTOYS_SECRET_KEY = "<secreto aleatorio de al menos 32 bytes>"
$env:KINGTOYS_HTTPS = "true"
python app.py
```

Genere el secreto con `python -c "import secrets; print(secrets.token_hex(32))"`. En producción use HTTPS y configure `KINGTOYS_HTTPS=true`; en desarrollo local HTTP manténgalo sin establecer para que la cookie funcione. Sin usuario y hash válidos, nadie puede iniciar sesión. Para crear otro vendedor, actualice las variables de entorno con el usuario y el hash de su contraseña.

Las sesiones caducan tras 30 minutos de inactividad y se renuevan durante el uso. Cerrar sesión elimina la cookie. Las ventas y consultas protegidas requieren autenticación.

## Seguridad OWASP

Consulte [docs/seguridad-owasp.md](docs/seguridad-owasp.md) para el checklist, revisión de los módulos y bibliografía APA.

## Dependencias

Instale Flask en el entorno virtual de su equipo (`python -m pip install Flask`) y ejecute `python app.py`. La base SQLite se crea localmente al iniciar y no debe subirse si contiene datos reales.
