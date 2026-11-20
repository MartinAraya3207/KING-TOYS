CREATE TABLE IF NOT EXISTS producto (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    precio INTEGER NOT NULL CHECK (precio > 0),
    stock_disponible INTEGER NOT NULL DEFAULT 0 CHECK (stock_disponible >= 0),
    categoria TEXT
);

CREATE TABLE IF NOT EXISTS venta (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    monto_total INTEGER NOT NULL CHECK (monto_total > 0),
    metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('tarjeta', 'efectivo', 'transferencia')),
    id_vendedor INTEGER
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL REFERENCES venta(id_venta),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario INTEGER NOT NULL CHECK (precio_unitario > 0)
);

CREATE TABLE IF NOT EXISTS reserva (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    usuario_instagram TEXT NOT NULL,
    fecha TEXT NOT NULL,
    monto_total INTEGER NOT NULL CHECK (monto_total > 0),
    comprobante_archivo TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente_validacion'
        CHECK (estado IN ('pendiente_validacion', 'lista_retiro', 'rechazada', 'retirada')),
    validada_por TEXT,
    fecha_validacion TEXT,
    fecha_retiro TEXT,
    id_venta INTEGER UNIQUE REFERENCES venta(id_venta)
);

CREATE TABLE IF NOT EXISTS detalle_reserva (
    id_detalle_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    id_reserva INTEGER NOT NULL REFERENCES reserva(id_reserva),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario INTEGER NOT NULL CHECK (precio_unitario > 0)
);

CREATE INDEX IF NOT EXISTS idx_reserva_usuario_estado
    ON reserva(usuario_instagram, estado);

INSERT OR IGNORE INTO producto (nombre, precio, stock_disponible, categoria) VALUES
('Álbum Stitch Panini', 4990, 12, 'Álbumes'),
('Sobre de láminas Panini', 990, 80, 'Álbumes'),
('Manga Berserk Vol. 1', 14990, 6, 'Manga'),
('Manga One Piece Vol. 102', 10990, 8, 'Manga'),
('Fig. Satoru Gojo JJK', 24990, 3, 'Figuras'),
('Funko Pop Batman Retro', 19990, 5, 'Figuras'),
('Auto Dodge Charger F&F', 3990, 10, 'Autos'),
('Bebida Monster Verde', 1890, 24, 'Bazar');