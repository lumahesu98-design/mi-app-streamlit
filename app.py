# Sistema de Gestión de Inventario - AGROINSUMOS LA COSECHA SAS
# Grupo 445A
# Aplicación desarrollada a partir del Avance 4.

import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SIGA - Agroinsumos La Cosecha", page_icon="🌱", layout="wide")


# -------------------------------------------------------------------
# Conexión a la base de datos
# -------------------------------------------------------------------
@st.cache_resource
def obtener_conexion():
    conexion = sqlite3.connect("clase.db", check_same_thread=False)
    return conexion


conexion = obtener_conexion()


# -------------------------------------------------------------------
# Inicialización segura: crea las tablas y la vista solo si no existen.
# Los datos iniciales se insertan únicamente cuando las tablas están vacías.
# -------------------------------------------------------------------
def inicializar_base_datos():
    cursor = conexion.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS productos (
        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        Unidad_medida TEXT NOT NULL,
        precio_unitario REAL NOT NULL,
        stock_minimo INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS movimientos (
        id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
        id_producto INTEGER NOT NULL,
        tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'salida')),
        cantidad INTEGER NOT NULL CHECK (cantidad > 0),
        fecha TEXT NOT NULL,
        id_proveedor INTEGER,
        id_cliente INTEGER,
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
        FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor),
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)

    # Datos de ejemplo: se cargan solo si cada tabla está vacía.
    if cursor.execute("SELECT COUNT(*) FROM proveedores").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO proveedores (nombre, telefono) VALUES (?, ?)",
            [
                ("Agroquimicos del Valle SAS", "6023755149"),
                ("Quimicos y Cultivos SAS", "3114814654"),
                ("Distribuidora las semillas", "3152197019"),
                ("Servicampo del Valle", "3155240239"),
                ("Semillas del Valle", "3102033186"),
                ("Sumitomo Chemiccal Colombia", "6023310800"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)",
            [
                ("Cooperativa Campesina Del Valle", "3165325046"),
                ("Ingenio Manuelita", "6023976060"),
                ("Ingenio Incauca", "6024183000"),
                ("Ingenio providencia", "6024183500"),
                ("Finca el Porvenir", "3172443279"),
                ("Finca la Esperanza", "3113293770"),
                ("Federación Nacional de cafeteros", "6013136600"),
                ("Agropecuaria San Jose", "3107868811"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO productos
               (nombre, Unidad_medida, precio_unitario, stock_minimo)
               VALUES (?, ?, ?, ?)""",
            [
                ("Semillas del Cafe", "kg", 40000, 2000),
                ("Fertilizante", "Bulto", 120000, 1000),
                ("Fungicida", "Lt", 45000, 25000),
                ("Semilla de Maiz", "kg", 12000, 2000),
                ("Urea Agricola", "kg", 150000, 2000),
                ("Incecticida", "Lt", 35000, 25000),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM movimientos").fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO movimientos
               (id_producto, tipo, cantidad, fecha, id_proveedor)
               VALUES (?, 'entrada', ?, ?, ?)""",
            [
                (1, 20000, "2026-09-30", 1),
                (2, 500, "2026-09-30", 2),
                (3, 800, "2026-09-30", 3),
                (4, 1000, "2026-09-28", 4),
                (5, 950, "2026-09-25", 5),
                (6, 17000, "2026-09-20", 6),
            ],
        )
        cursor.executemany(
            """INSERT INTO movimientos
               (id_producto, tipo, cantidad, fecha, id_cliente)
               VALUES (?, 'salida', ?, ?, ?)""",
            [
                (1, 8000, "2026-10-03", 1),
                (2, 1000, "2026-10-03", 2),
                (3, 1000, "2026-10-03", 3),
                (4, 1100, "2026-10-03", 4),
                (5, 1000, "2026-10-03", 5),
                (6, 800, "2026-10-03", 6),
            ],
        )

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS vw_inventario AS
    SELECT
        p.id_producto,
        p.nombre,
        p.Unidad_medida,
        p.stock_minimo,
        COALESCE(
            SUM(
                CASE
                    WHEN m.tipo = 'entrada' THEN m.cantidad
                    WHEN m.tipo = 'salida' THEN -m.cantidad
                    ELSE 0
                END
            ), 0
        ) AS stock_actual
    FROM productos p
    LEFT JOIN movimientos m ON p.id_producto = m.id_producto
    GROUP BY p.id_producto, p.nombre, p.Unidad_medida, p.stock_minimo;
    """)

    conexion.commit()


inicializar_base_datos()


# -------------------------------------------------------------------
# Funciones originales del Avance 4
# -------------------------------------------------------------------
def registrar_entrada(id_producto, cantidad, fecha=None, id_proveedor=None):
    try:
        if not isinstance(cantidad, int) or cantidad <= 0:
            return False, "La cantidad debe ser un número entero positivo."

        if not isinstance(id_producto, int) or id_producto <= 0:
            return False, "El ID del producto no es válido."

        if fecha is None:
            fecha = date.today().isoformat()

        cursor = conexion.cursor()

        producto = cursor.execute(
            "SELECT id_producto FROM productos WHERE id_producto = ?",
            (id_producto,)
        ).fetchone()

        if producto is None:
            return False, "El producto no existe."

        if id_proveedor is not None:
            proveedor = cursor.execute(
                "SELECT id_proveedor FROM proveedores WHERE id_proveedor = ?",
                (id_proveedor,)
            ).fetchone()

            if proveedor is None:
                return False, "El proveedor no existe."

        cursor.execute("""
            INSERT INTO movimientos
            (id_producto, tipo, cantidad, fecha, id_proveedor)
            VALUES (?, 'entrada', ?, ?, ?)
        """, (id_producto, cantidad, fecha, id_proveedor))

        conexion.commit()

        return True, "Entrada registrada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, str(error)


def registrar_salida(id_producto, cantidad, fecha=None, id_cliente=None):
    try:
        if not isinstance(cantidad, int) or cantidad <= 0:
            return False, "La cantidad debe ser un número entero positivo."

        if not isinstance(id_producto, int) or id_producto <= 0:
            return False, "El ID del producto no es válido."

        if fecha is None:
            fecha = date.today().isoformat()

        cursor = conexion.cursor()

        producto = cursor.execute(
            "SELECT id_producto FROM productos WHERE id_producto = ?",
            (id_producto,)
        ).fetchone()

        if producto is None:
            return False, "El producto no existe."

        inventario = cursor.execute("""
            SELECT stock_actual
            FROM vw_inventario
            WHERE id_producto = ?
        """, (id_producto,)).fetchone()

        stock = inventario[0] if inventario else 0

        if cantidad > stock:
            return False, "No hay suficiente inventario para realizar la salida."

        if id_cliente is not None:
            cliente = cursor.execute(
                "SELECT id_cliente FROM clientes WHERE id_cliente = ?",
                (id_cliente,)
            ).fetchone()

            if cliente is None:
                return False, "El cliente no existe."

        cursor.execute("""
            INSERT INTO movimientos
            (id_producto, tipo, cantidad, fecha, id_cliente)
            VALUES (?, 'salida', ?, ?, ?)
        """, (id_producto, cantidad, fecha, id_cliente))

        conexion.commit()

        return True, "Salida registrada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, str(error)


def consultar_inventario(unidad_medida=None):
    consulta = "SELECT * FROM vw_inventario"
    parametros = []

    if unidad_medida is not None:
        consulta += " WHERE Unidad_medida = ?"
        parametros.append(unidad_medida)

    return pd.read_sql_query(consulta, conexion, params=parametros)


def alertas_stock_bajo(minimo):
    if not isinstance(minimo, (int, float)) or minimo < 0:
        raise ValueError("El mínimo debe ser un número positivo.")

    consulta = """
        SELECT *
        FROM vw_inventario
        WHERE stock_actual <= ?
    """

    return pd.read_sql_query(consulta, conexion, params=(minimo,))


def consultar_movimientos_proveedor(id_proveedor):
    cursor = conexion.cursor()

    proveedor = cursor.execute(
        "SELECT id_proveedor FROM proveedores WHERE id_proveedor = ?",
        (id_proveedor,)
    ).fetchone()

    if proveedor is None:
        print("El proveedor no existe.")
        return pd.DataFrame()

    consulta = """
        SELECT
            m.id_movimiento,
            p.nombre AS producto,
            m.tipo,
            m.cantidad,
            m.fecha,
            m.id_proveedor
        FROM movimientos m
        INNER JOIN productos p
            ON m.id_producto = p.id_producto
        WHERE m.id_proveedor = ?
    """

    return pd.read_sql_query(consulta, conexion, params=(id_proveedor,))


def registrar_lote_entradas(entradas):
    cursor = conexion.cursor()

    try:
        cursor.execute("BEGIN")

        for id_producto, cantidad, fecha, id_proveedor in entradas:
            if not isinstance(cantidad, int) or cantidad <= 0:
                raise ValueError("La cantidad debe ser positiva.")

            producto = cursor.execute(
                "SELECT id_producto FROM productos WHERE id_producto = ?",
                (id_producto,)
            ).fetchone()

            if producto is None:
                raise ValueError(f"El producto {id_producto} no existe.")

            if id_proveedor is not None:
                proveedor = cursor.execute(
                    "SELECT id_proveedor FROM proveedores WHERE id_proveedor = ?",
                    (id_proveedor,)
                ).fetchone()

                if proveedor is None:
                    raise ValueError("El proveedor no existe.")

            cursor.execute("""
                INSERT INTO movimientos
                (id_producto, tipo, cantidad, fecha, id_proveedor)
                VALUES (?, 'entrada', ?, ?, ?)
            """, (id_producto, cantidad, fecha, id_proveedor))

        conexion.commit()
        return True, "Todas las entradas fueron registradas correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Operación cancelada. Se realizó rollback: {error}"


# -------------------------------------------------------------------
# Interfaz Streamlit
# -------------------------------------------------------------------
st.title("🌱 SIGA - Sistema de Gestión de Inventario")
st.subheader("AGROINSUMOS LA COSECHA SAS")
st.caption("Grupo 445A | Gestión de productos, entradas, salidas y alertas de inventario")

tab_inicio, tab_movimiento, tab_inventario, tab_alertas = st.tabs(
    ["Inicio", "Registrar movimiento", "Inventario", "Alertas"]
)

with tab_inicio:
    inventario = consultar_inventario()
    total_productos = len(inventario)
    total_unidades = int(inventario["stock_actual"].sum()) if not inventario.empty else 0
    productos_bajo_minimo = int(
        (inventario["stock_actual"] <= inventario["stock_minimo"]).sum()
    ) if not inventario.empty else 0

    st.subheader("Resumen general")
    col1, col2, col3 = st.columns(3)
    col1.metric("Productos registrados", total_productos)
    col2.metric("Unidades en inventario", f"{total_unidades:,}")
    col3.metric("Productos en nivel mínimo", productos_bajo_minimo)

    st.write("Bienvenido al sistema de gestión de inventario. Desde las pestañas puedes registrar movimientos, consultar existencias y revisar alertas de stock.")

with tab_movimiento:
    st.subheader("Registrar entrada o salida")
    productos = pd.read_sql_query(
        "SELECT id_producto, nombre FROM productos ORDER BY nombre",
        conexion
    )

    if productos.empty:
        st.warning("No hay productos registrados.")
    else:
        with st.form("formulario_movimiento"):
            producto_seleccionado = st.selectbox(
                "Selecciona el producto",
                productos["id_producto"].tolist(),
                format_func=lambda id_producto: productos.loc[
                    productos["id_producto"] == id_producto, "nombre"
                ].iloc[0],
            )
            tipo_movimiento = st.selectbox("Tipo de movimiento", ["entrada", "salida"])
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            enviar = st.form_submit_button("Registrar movimiento")

        if enviar:
            if tipo_movimiento == "entrada":
                resultado, mensaje = registrar_entrada(
                    int(producto_seleccionado), int(cantidad)
                )
            else:
                resultado, mensaje = registrar_salida(
                    int(producto_seleccionado), int(cantidad)
                )

            if resultado:
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)

with tab_inventario:
    st.subheader("Inventario actual")
    inventario_completo = consultar_inventario()
    unidades = ["Todas"] + sorted(
        inventario_completo["Unidad_medida"].dropna().unique().tolist()
    ) if not inventario_completo.empty else ["Todas"]

    filtro_unidad = st.selectbox("Filtrar por unidad de medida", unidades)

    if filtro_unidad == "Todas":
        inventario_filtrado = inventario_completo
    else:
        inventario_filtrado = consultar_inventario(filtro_unidad)

    st.dataframe(inventario_filtrado, use_container_width=True, hide_index=True)

with tab_alertas:
    st.subheader("Alertas de inventario bajo")
    inventario_completo = consultar_inventario()
    maximo_stock = int(inventario_completo["stock_actual"].max()) if not inventario_completo.empty else 100
    maximo_stock = max(maximo_stock, 1)
    minimo_alerta = st.slider(
        "Mostrar productos con stock igual o inferior a:",
        min_value=0,
        max_value=maximo_stock,
        value=min(2000, maximo_stock),
        step=1,
    )

    alertas = alertas_stock_bajo(minimo_alerta)
    if alertas.empty:
        st.success("No hay productos por debajo del nivel seleccionado.")
    else:
        st.dataframe(alertas, use_container_width=True, hide_index=True)
        grafico = alertas.set_index("nombre")[["stock_actual"]]
        st.bar_chart(grafico)
