# KING-TOYS

## Configuración MySQL

1. Instalar las dependencias:

pip install -r requirements.txt

2. Crear un archivo .env en la raíz del proyecto:

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=kingtoyspos

3. Ejecutar database/kingtoys_v1.sql en MySQL Workbench.

4. Iniciar la aplicación:

python app.py

## Estado de integración

- [x] Configuración de conexión MySQL.
- [x] Creación del esquema y tablas.
- [x] Catálogo inicial de 8 productos.
- [ ] Migración del módulo de ventas (actualmente usa SQLite).
- [ ] Integración del inventario.
- [ ] Autenticación y cierre de sesión.
- [ ] Integración de reservas.
