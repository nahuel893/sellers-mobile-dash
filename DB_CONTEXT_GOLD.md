# Contexto IA - Capa Gold (Data Warehouse)

## Resumen General

Data Warehouse con arquitectura **Medallion** (Bronze → Silver → Gold).
La capa **Gold** contiene el modelo dimensional (Star Schema) optimizado para consultas analíticas.

### Estadísticas
| Tabla | Registros |
|-------|-----------|
| dim_articulo | 3,255 |
| dim_cliente | 15,942 |
| dim_vendedor | 144 |
| dim_sucursal | 14 |
| dim_deposito | 15 |
| dim_tiempo | (calendario) |
| fact_ventas | 7,070,292 |
| fact_stock | 126,424 |

---

## Tablas de Dimensiones

### gold.dim_articulo
Catálogo de artículos/productos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_articulo` | integer | PK - ID del artículo |
| `des_articulo` | varchar(200) | Descripción del artículo |
| `marca` | varchar(150) | Marca del producto |
| `generico` | varchar(150) | Categoría genérica |
| `calibre` | varchar(150) | Calibre/tamaño |
| `proveedor` | varchar(150) | Proveedor |
| `unidad_negocio` | varchar(150) | Unidad de negocio |
| `factor_hectolitros` | numeric(12,8) | Factor conversión a HTLs |

**Genéricos disponibles (27):**
- CERVEZAS, AGUAS DANONE, VINOS CCU, SIDRAS Y LICORES (FV1)
- FRATELLI B, VINOS, JUGOS, VINOS FINOS (FV4)
- GASEOSAS, ENERGIZANTES, ESPIRITUOSOS, APERITIVOS
- MARKETING, ENVASES CCU, EQUIPOS DE FRIO, otros

---

### gold.dim_cliente
Clientes/puntos de venta. **Clave compuesta: id_cliente + id_sucursal**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_cliente` | integer | PK - ID del cliente |
| `razon_social` | varchar(150) | Razón social |
| `fantasia` | varchar(150) | Nombre de fantasía |
| `id_sucursal` | integer | FK - Sucursal que lo atiende |
| `des_sucursal` | varchar(100) | Descripción sucursal |
| `id_canal_mkt` | integer | Canal de marketing |
| `des_canal_mkt` | varchar(100) | Descripción canal |
| `id_segmento_mkt` | integer | Segmento de marketing |
| `des_segmento_mkt` | varchar(100) | Descripción segmento |
| `id_subcanal_mkt` | integer | Subcanal |
| `des_subcanal_mkt` | varchar(100) | Descripción subcanal |
| `id_ruta_fv1` | integer | Ruta FV1 (Preventa) |
| `des_personal_fv1` | varchar(150) | Vendedor FV1 |
| `id_ruta_fv4` | integer | Ruta FV4 (Autoventa) |
| `des_personal_fv4` | varchar(150) | Vendedor FV4 |
| `id_ramo` | integer | Ramo/tipo de negocio |
| `des_ramo` | varchar(100) | Descripción ramo |
| `id_localidad` | integer | Localidad |
| `des_localidad` | varchar(100) | Descripción localidad |
| `id_provincia` | varchar(10) | Código provincia |
| `des_provincia` | varchar(100) | Descripción provincia |
| `latitud` | numeric(15,6) | Coordenada |
| `longitud` | numeric(15,6) | Coordenada |
| `id_lista_precio` | integer | Lista de precios |
| `des_lista_precio` | varchar(100) | Descripción lista |
| `anulado` | boolean | Cliente anulado |

**Canales de Marketing:**
| ID | Descripción |
|----|-------------|
| 1 | CANAL GENERAL |
| 2 | CANAL MAY (Mayoristas) |
| 3 | DIRECTA AL CONSUMIDOR |
| 4 | CANAL ON (On Premise) |
| 5 | CANAL AUTOSERVICIO |
| 6 | CANAL DTT |

**Listas de Precio:** 1, 3, 4 (ON Premise), 5, 6, 7, 8, 9, 11, 12, 13, 14

---

### gold.dim_vendedor
Vendedores/preventistas. **Clave compuesta: id_vendedor + id_sucursal**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_vendedor` | integer | PK - ID del vendedor |
| `des_vendedor` | varchar(150) | Nombre del vendedor |
| `id_fuerza_ventas` | integer | Fuerza de ventas (1 o 4) |
| `id_sucursal` | integer | Sucursal |
| `des_sucursal` | varchar(100) | Descripción sucursal |

**Fuerzas de Venta:**
| ID | Nombre | Genéricos que vende |
|----|--------|---------------------|
| 1 | FV1 - Preventa | CERVEZAS, AGUAS DANONE, VINOS CCU, SIDRAS Y LICORES |
| 4 | FV4 - Autoventa | FRATELLI B, VINOS, JUGOS, VINOS FINOS |

---

### gold.dim_sucursal
Sucursales de la empresa.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_sucursal` | integer | PK - ID sucursal |
| `descripcion` | varchar(100) | Nombre sucursal |

**Sucursales (14):**
| ID | Descripción |
|----|-------------|
| 1 | CASA CENTRAL |
| 3 | SUCURSAL CAFAYATE |
| 4 | SUCURSAL JOAQUIN V GONZALEZ |
| 5 | SUCURSAL METAN |
| 6 | SUCURSAL ORAN |
| 7 | SUCURSAL TARTAGAL |
| 9 | SUCURSAL PERICO |
| 10 | SUCURSAL LIBERTADOR |
| 11 | SUCURSAL MAIMARA |
| 12 | SUCURSAL HUMAHUACA |
| 13 | SUCURSAL ABRA PAMPA |
| 14 | SUCURSAL LA QUIACA |
| 15 | SUCURSAL SAN PEDRO |
| 16 | SUCURSAL GUEMES |

---

### gold.dim_deposito
Depósitos de stock.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_deposito` | integer | PK - ID depósito |
| `descripcion` | varchar(255) | Nombre depósito |
| `id_sucursal` | integer | FK - Sucursal |
| `des_sucursal` | varchar(100) | Descripción sucursal |

---

### gold.dim_tiempo
Calendario para análisis temporal.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `fecha` | date | PK - Fecha |
| `dia` | integer | Día del mes |
| `dia_semana` | integer | Día de la semana (1-7) |
| `nombre_dia` | varchar(15) | Nombre del día |
| `semana` | integer | Semana del año |
| `mes` | integer | Mes (1-12) |
| `nombre_mes` | varchar(15) | Nombre del mes |
| `trimestre` | integer | Trimestre (1-4) |
| `anio` | integer | Año |

---

## Tablas de Hechos

### gold.fact_ventas
Líneas de venta (comprobantes). **Granularidad: una fila por línea de comprobante.**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | integer | PK - ID auto |
| `id_cliente` | integer | FK - Cliente |
| `id_articulo` | integer | FK - Artículo |
| `id_vendedor` | integer | FK - Vendedor |
| `id_sucursal` | integer | FK - Sucursal |
| `fecha_comprobante` | date | Fecha de la venta |
| `id_documento` | varchar(20) | Tipo documento |
| `letra` | char(1) | Letra factura |
| `serie` | integer | Serie |
| `nro_doc` | integer | Número documento |
| `anulado` | boolean | Comprobante anulado |
| `cantidades_con_cargo` | numeric(15,4) | Cantidad con cargo |
| `cantidades_sin_cargo` | numeric(15,4) | Cantidad sin cargo (bonif) |
| `cantidades_total` | numeric(15,4) | **Cantidad total (usar este)** |
| `subtotal_neto` | numeric(15,4) | Subtotal neto |
| `subtotal_final` | numeric(15,4) | **Importe final (usar este)** |
| `bonificacion` | numeric(8,4) | % bonificación |
| `cantidad_total_htls` | numeric(15,4) | **Cantidad en hectolitros** |

---

### gold.fact_stock
Stock por depósito/artículo/fecha. **Granularidad: una fila por depósito/artículo/día.**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | integer | PK - ID auto |
| `date_stock` | date | Fecha del stock |
| `id_deposito` | integer | FK - Depósito |
| `id_articulo` | integer | FK - Artículo |
| `cant_bultos` | numeric(15,4) | Cantidad en bultos |
| `cant_unidades` | numeric(15,4) | Cantidad en unidades |
| `cantidad_total_htls` | numeric(15,4) | Cantidad en hectolitros |

---

## Claves Compuestas (IMPORTANTE)

Los IDs de **vendedor** y **cliente** NO son únicos globalmente, son únicos **por sucursal**.

```sql
-- ✅ CORRECTO: JOIN con clave compuesta
JOIN gold.dim_vendedor dv
  ON fv.id_vendedor = dv.id_vendedor
  AND fv.id_sucursal = dv.id_sucursal

JOIN gold.dim_cliente dc
  ON fv.id_cliente = dc.id_cliente
  AND fv.id_sucursal = dc.id_sucursal

-- ❌ INCORRECTO: JOIN solo por ID
JOIN gold.dim_vendedor dv ON fv.id_vendedor = dv.id_vendedor
```

---

## Consultas de Ejemplo

### Ventas por Genérico/Marca/Año
```sql
SELECT
    da.generico,
    da.marca,
    EXTRACT(YEAR FROM fv.fecha_comprobante) AS anio,
    SUM(fv.cantidades_total) AS volumen,
    SUM(fv.subtotal_final) AS importe
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da ON fv.id_articulo = da.id_articulo
GROUP BY da.generico, da.marca, anio
ORDER BY anio, volumen DESC;
```

### Ventas por Sucursal/Vendedor
```sql
SELECT
    ds.descripcion AS sucursal,
    dv.des_vendedor,
    SUM(fv.cantidades_total) AS volumen
FROM gold.fact_ventas fv
JOIN gold.dim_sucursal ds ON fv.id_sucursal = ds.id_sucursal
JOIN gold.dim_vendedor dv
  ON fv.id_vendedor = dv.id_vendedor
  AND fv.id_sucursal = dv.id_sucursal
GROUP BY ds.descripcion, dv.des_vendedor
ORDER BY ds.descripcion, volumen DESC;
```

### Ventas por Canal de Cliente
```sql
SELECT
    dc.des_canal_mkt,
    da.generico,
    SUM(fv.cantidades_total) AS volumen
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da ON fv.id_articulo = da.id_articulo
JOIN gold.dim_cliente dc
  ON fv.id_cliente = dc.id_cliente
  AND fv.id_sucursal = dc.id_sucursal
GROUP BY dc.des_canal_mkt, da.generico
ORDER BY dc.des_canal_mkt, volumen DESC;
```

### Ventas ON Premise (Lista precio 4)
```sql
SELECT
    da.generico,
    da.marca,
    SUM(fv.cantidad_total_htls) AS htls
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da ON fv.id_articulo = da.id_articulo
JOIN gold.dim_cliente dc
  ON fv.id_cliente = dc.id_cliente
  AND fv.id_sucursal = dc.id_sucursal
WHERE dc.id_lista_precio = 4
GROUP BY da.generico, da.marca;
```

### Stock actual por Depósito
```sql
SELECT
    dd.descripcion AS deposito,
    da.generico,
    SUM(fs.cant_unidades) AS unidades
FROM gold.fact_stock fs
JOIN gold.dim_articulo da ON fs.id_articulo = da.id_articulo
JOIN gold.dim_deposito dd ON fs.id_deposito = dd.id_deposito
WHERE fs.date_stock = (SELECT MAX(date_stock) FROM gold.fact_stock)
GROUP BY dd.descripcion, da.generico
ORDER BY dd.descripcion, unidades DESC;
```

---

## Notas Importantes

1. **Usar `cantidades_total`** para volumen, no `cantidades_con_cargo`
2. **Usar `subtotal_final`** para importes
3. **Usar `cantidad_total_htls`** para hectolitros (cuando esté poblado)
4. **No filtrar por `anulado`** - incluir anulados en cálculos
5. **Siempre usar clave compuesta** para JOINs con dim_vendedor y dim_cliente
6. **Lista precio 4** = ON Premise (bares, restaurantes)
7. **FV1** = Preventa (cervezas, aguas), **FV4** = Autoventa (vinos, Fratelli)
