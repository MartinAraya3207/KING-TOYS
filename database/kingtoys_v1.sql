
-- =====================================================
-- KINGTOYSPOS
-- Base de datos: kingtoyspos
-- MySQL 9.7
-- =====================================================

CREATE DATABASE IF NOT EXISTS kingtoyspos
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE kingtoyspos;
    
-- =====================================================
-- 1. TABLA VENDEDOR
-- =====================================================

CREATE TABLE IF NOT EXISTS vendedor (
    id_vendedor INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- 2. TABLA CLIENTE
-- =====================================================

CREATE TABLE IF NOT EXISTS cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario_instagram VARCHAR(100),
    telefono VARCHAR(20),
    correo VARCHAR(120),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- 3. TABLA PRODUCTO
-- =====================================================

CREATE TABLE IF NOT EXISTS producto (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(80),
    precio DECIMAL(12,2) NOT NULL,
    stock_disponible INT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_producto_precio
        CHECK (precio >= 0),

    CONSTRAINT chk_producto_stock
        CHECK (stock_disponible >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 4. TABLA RESERVA
-- =====================================================

CREATE TABLE IF NOT EXISTS reserva (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    codigo_reserva VARCHAR(30) NOT NULL UNIQUE,
    id_cliente INT NOT NULL,
    id_vendedor INT NOT NULL,
    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_retiro DATETIME NULL,
    monto_total DECIMAL(12,2) NOT NULL DEFAULT 0,
    monto_abonado DECIMAL(12,2) NOT NULL DEFAULT 0,
    estado ENUM(
        'pendiente',
        'confirmada',
        'retirada',
        'cancelada'
    ) NOT NULL DEFAULT 'pendiente',

    CONSTRAINT fk_reserva_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_cliente),

    CONSTRAINT fk_reserva_vendedor
        FOREIGN KEY (id_vendedor)
        REFERENCES vendedor(id_vendedor),

    CONSTRAINT chk_reserva_monto
        CHECK (monto_total >= 0 AND monto_abonado >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 5. TABLA DETALLE_RESERVA
-- =====================================================

CREATE TABLE IF NOT EXISTS detalle_reserva (
    id_detalle_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_detalle_reserva_reserva
        FOREIGN KEY (id_reserva)
        REFERENCES reserva(id_reserva),

    CONSTRAINT fk_detalle_reserva_producto
        FOREIGN KEY (id_producto)
        REFERENCES producto(id_producto),

    CONSTRAINT chk_detalle_reserva_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_detalle_reserva_precio
        CHECK (precio_unitario >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 6. TABLA VENTA
-- =====================================================

CREATE TABLE IF NOT EXISTS venta (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NULL,
    id_vendedor INT NOT NULL,
    id_reserva INT NULL UNIQUE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto_total DECIMAL(12,2) NOT NULL,
    metodo_pago ENUM(
        'efectivo',
        'tarjeta',
        'transferencia'
    ) NOT NULL,

    CONSTRAINT fk_venta_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_cliente),

    CONSTRAINT fk_venta_vendedor
        FOREIGN KEY (id_vendedor)
        REFERENCES vendedor(id_vendedor),

    CONSTRAINT fk_venta_reserva
        FOREIGN KEY (id_reserva)
        REFERENCES reserva(id_reserva),

    CONSTRAINT chk_venta_monto
        CHECK (monto_total >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 7. TABLA DETALLE_VENTA
-- =====================================================

CREATE TABLE IF NOT EXISTS detalle_venta (
    id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_detalle_venta_venta
        FOREIGN KEY (id_venta)
        REFERENCES venta(id_venta),

    CONSTRAINT fk_detalle_venta_producto
        FOREIGN KEY (id_producto)
        REFERENCES producto(id_producto),

    CONSTRAINT chk_detalle_venta_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_detalle_venta_precio
        CHECK (precio_unitario >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- INDICES ADICIONALES
-- =====================================================

CREATE INDEX idx_reserva_estado
ON reserva(estado);

CREATE INDEX idx_reserva_fecha
ON reserva(fecha_reserva);

CREATE INDEX idx_venta_fecha
ON venta(fecha);

CREATE INDEX idx_producto_nombre
ON producto(nombre);

-- =====================================================

-- =====================================================
-- =====================================================
-- DATOS DE PRUEBA
-- =====================================================

INSERT INTO vendedor (usuario, password_hash, nombre)
SELECT 'vendedor_prueba', 'HASH_DE_PRUEBA_SIN_AUTENTICACION', 'Vendedor de prueba'
WHERE NOT EXISTS (
    SELECT 1 FROM vendedor WHERE usuario = 'vendedor_prueba'
);

INSERT INTO cliente (nombre, usuario_instagram, telefono, correo)
SELECT 'Cliente de prueba', 'cliente_prueba', NULL, 'cliente@ejemplo.com'
WHERE NOT EXISTS (
    SELECT 1 FROM cliente WHERE usuario_instagram = 'cliente_prueba'
);

-- CATALOGO INICIAL DE PRODUCTOS
-- =====================================================

INSERT INTO producto
(id_producto, nombre, precio, stock_disponible, categoria)
VALUES
(1, 'Álbum Stitch Panini', 4990, 12, 'Álbumes'),
(2, 'Sobre de láminas Panini', 990, 80, 'Álbumes'),
(3, 'Manga Berserk Vol. 1', 14990, 6, 'Manga'),
(4, 'Manga One Piece Vol. 102', 10990, 8, 'Manga'),
(5, 'Fig. Satoru Gojo JJK', 24990, 3, 'Figuras'),
(6, 'Funko Pop Batman Retro', 19990, 5, 'Figuras'),
(7, 'Auto Dodge Charger F&F', 3990, 10, 'Autos'),
(8, 'Bebida Monster Verde', 1890, 24, 'Bazar');

-- =====================================================
-- FIN DEL SCRIPT KINGTOYSPOS V1
-- =====================================================
