/**
 * VentasMapaPage — página full-screen del mapa de burbujas de ventas.
 *
 * Layout:
 *   ┌─────────────────────────────────────────┐
 *   │ TopBar: título + toggle métrica + botón filtros │
 *   ├─────────────────────────────────────────┤
 *   │ Mapa full-screen (react-map-gl + deck.gl) │
 *   └─────────────────────────────────────────┘
 *   Drawer de filtros desde la derecha.
 *
 * Target: desktop ≥ 1280px. Tema oscuro.
 */
import { useState, useCallback, useReducer } from 'react';
import VentasMapa from '../../components/ventas-mapa/VentasMapa';
import VentasMapaFiltros from '../../components/ventas-mapa/VentasMapaFiltros';
import VentasMapaMetricaToggle from '../../components/ventas-mapa/VentasMapaMetricaToggle';
import VentasMapaModoToggle from '../../components/ventas-mapa/VentasMapaModoToggle';
import VentasMapaZonasCards from '../../components/ventas-mapa/VentasMapaZonasCards';
import { useVentasFiltros } from '../../hooks/ventas-mapa/use-ventas-filtros';
import { useVentasClientes } from '../../hooks/ventas-mapa/use-ventas-clientes';
import { useVentasZonas } from '../../hooks/ventas-mapa/use-ventas-zonas';
import { useVentasCompro } from '../../hooks/ventas-mapa/use-ventas-compro';
import type {
  VentasFiltrosState,
  VentasClientesParams,
  VentasMetrica,
  VentasZonasParams,
  VentasMapaModo,
  CalorSubmodo,
  VentasComproParams,
} from '../../types/ventas';
import { DARK, ZONE_BADGE_THRESHOLD } from '../../lib/ventas-constants';
import { Link } from 'react-router';

// ---------------------------------------------------------------------------
// Estado inicial de filtros
// ---------------------------------------------------------------------------

function getDefaultFechas(): { fecha_ini: string; fecha_fin: string } {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const toISO = (d: Date) => d.toISOString().split('T')[0];
  return {
    fecha_ini: toISO(firstDay),
    fecha_fin: toISO(now),
  };
}

const { fecha_ini: DEFAULT_FECHA_INI, fecha_fin: DEFAULT_FECHA_FIN } = getDefaultFechas();

const FILTROS_INICIALES: VentasFiltrosState = {
  fecha_ini: DEFAULT_FECHA_INI,
  fecha_fin: DEFAULT_FECHA_FIN,
  canal: [],
  subcanal: [],
  localidad: [],
  lista_precio: [],
  tipo_sucursal: 'TODAS',
  sucursal_ids: [],
  genericos: [],
  marcas: [],
  fv: 'AMBAS',
  rutas: [],
  preventistas: [],
  metrica: 'bultos',
  zonas_agrupacion: 'OCULTAS',
};

// ---------------------------------------------------------------------------
// Reducer — estado de filtros separado del estado "aplicado"
// ---------------------------------------------------------------------------

type FiltrosAction =
  | { type: 'SET'; filtros: VentasFiltrosState }
  | { type: 'RESET' };

function filtrosReducer(_state: VentasFiltrosState, action: FiltrosAction): VentasFiltrosState {
  switch (action.type) {
    case 'SET':
      return action.filtros;
    case 'RESET':
      return FILTROS_INICIALES;
  }
}

// ---------------------------------------------------------------------------
// Conversión filtros → params para el endpoint
// ---------------------------------------------------------------------------

function filtrosToParams(filtros: VentasFiltrosState): VentasClientesParams {
  return {
    fecha_ini: filtros.fecha_ini,
    fecha_fin: filtros.fecha_fin,
    metrica: filtros.metrica,
    fv: filtros.fv !== 'AMBAS' ? filtros.fv : undefined,
    canal: filtros.canal.length === 1 ? filtros.canal[0] : undefined,
    subcanal: filtros.subcanal.length === 1 ? filtros.subcanal[0] : undefined,
    localidad: filtros.localidad.length === 1 ? filtros.localidad[0] : undefined,
    lista_precio: filtros.lista_precio.length === 1 ? filtros.lista_precio[0] : undefined,
    sucursal_id: filtros.sucursal_ids.length === 1 ? filtros.sucursal_ids[0] : undefined,
    ruta: filtros.rutas.length === 1 ? filtros.rutas[0] : undefined,
    preventista: filtros.preventistas.length === 1 ? filtros.preventistas[0] : undefined,
    genericos: filtros.genericos.length > 0 ? filtros.genericos : undefined,
    marcas: filtros.marcas.length > 0 ? filtros.marcas : undefined,
  };
}

function filtrosToZonasParams(filtros: VentasFiltrosState): VentasZonasParams | null {
  if (filtros.zonas_agrupacion === 'OCULTAS') return null;
  return {
    ...filtrosToParams(filtros),
    agrupacion: filtros.zonas_agrupacion,
  };
}

function filtrosToComproParams(filtros: VentasFiltrosState): VentasComproParams {
  return {
    fecha_ini: filtros.fecha_ini,
    fecha_fin: filtros.fecha_fin,
    fv: filtros.fv !== 'AMBAS' ? filtros.fv : undefined,
    canal: filtros.canal.length === 1 ? filtros.canal[0] : undefined,
    subcanal: filtros.subcanal.length === 1 ? filtros.subcanal[0] : undefined,
    localidad: filtros.localidad.length === 1 ? filtros.localidad[0] : undefined,
    lista_precio: filtros.lista_precio.length === 1 ? filtros.lista_precio[0] : undefined,
    sucursal_id: filtros.sucursal_ids.length === 1 ? filtros.sucursal_ids[0] : undefined,
    ruta: filtros.rutas.length === 1 ? filtros.rutas[0] : undefined,
    preventista: filtros.preventistas.length === 1 ? filtros.preventistas[0] : undefined,
  };
}

// ---------------------------------------------------------------------------
// Página
// ---------------------------------------------------------------------------

export default function VentasMapaPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Modo de visualización del mapa
  const [modo, setModo] = useState<VentasMapaModo>('burbujas');
  const [calorSubmodo, setCalorSubmodo] = useState<CalorSubmodo>('difuso');

  // Filtros del drawer (borrador)
  const [filtrosDraft, dispatchFiltros] = useReducer(filtrosReducer, FILTROS_INICIALES);

  // Filtros aplicados (los que realmente generan el fetch)
  const [filtrosAplicados, setFiltrosAplicados] = useState<VentasFiltrosState>(FILTROS_INICIALES);

  // Métrica se cambia sin necesidad de reabrir el drawer
  const handleMetricaChange = useCallback((metrica: VentasMetrica) => {
    const next = { ...filtrosAplicados, metrica };
    setFiltrosAplicados(next);
    dispatchFiltros({ type: 'SET', filtros: next });
  }, [filtrosAplicados]);

  // Opciones de filtros (single call, sin cascade)
  const { data: opciones, isLoading: opcionesLoading } = useVentasFiltros();

  // Datos del mapa — se cargan con los filtros aplicados
  const params = filtrosToParams(filtrosAplicados);
  const { data: clientes, isLoading: clientesLoading, error: clientesError } = useVentasClientes(params);

  // Zonas — solo se cargan si la agrupación no es OCULTAS
  const zonasParams = filtrosToZonasParams(filtrosAplicados);
  const { data: zonas, isLoading: zonasLoading } = useVentasZonas(zonasParams);

  // Compro — solo se carga cuando modo=compro
  const comproParams: VentasComproParams | null = modo === 'compro'
    ? filtrosToComproParams(filtrosAplicados)
    : null;
  const { data: dataCompro, isLoading: comproLoading } = useVentasCompro(comproParams);

  const handleAplicar = useCallback(() => {
    setFiltrosAplicados(filtrosDraft);
  }, [filtrosDraft]);

  const handleLimpiar = useCallback(() => {
    dispatchFiltros({ type: 'RESET' });
    setFiltrosAplicados(FILTROS_INICIALES);
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: DARK.bg,
        color: DARK.text,
        overflow: 'hidden',
      }}
    >
      {/* Top bar */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '10px 16px',
          backgroundColor: DARK.card,
          borderBottom: `1px solid ${DARK.border}`,
          flexShrink: 0,
          zIndex: 100,
        }}
      >
        {/* Volver */}
        <Link
          to="/"
          style={{
            color: DARK.textSecondary,
            textDecoration: 'none',
            fontSize: '20px',
            lineHeight: 1,
            display: 'flex',
            alignItems: 'center',
          }}
          title="Volver al inicio"
        >
          ←
        </Link>

        <h1
          style={{
            fontSize: '15px',
            fontWeight: '700',
            color: DARK.text,
            margin: 0,
            flexShrink: 0,
          }}
        >
          Mapa de Ventas
        </h1>

        {/* Fechas aplicadas */}
        <span
          style={{
            fontSize: '11px',
            color: DARK.textMuted,
            flexShrink: 0,
          }}
        >
          {filtrosAplicados.fecha_ini} → {filtrosAplicados.fecha_fin}
        </span>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Estado de carga */}
        {(clientesLoading || zonasLoading || comproLoading) && (
          <span style={{ fontSize: '12px', color: DARK.textMuted }}>
            {clientesLoading ? 'Cargando clientes…' : zonasLoading ? 'Cargando zonas…' : 'Cargando compro…'}
          </span>
        )}

        {clientesError && (
          <span style={{ fontSize: '12px', color: DARK.accentRed }}>
            Error al cargar datos
          </span>
        )}

        {/* Contador */}
        {!clientesLoading && clientes && (
          <span style={{ fontSize: '12px', color: DARK.textSecondary }}>
            {clientes.length.toLocaleString('es-AR')} clientes
          </span>
        )}

        {/* Toggle modo */}
        <VentasMapaModoToggle value={modo} onChange={setModo} />

        {/* Toggle métrica — solo visible en modo burbujas */}
        {modo === 'burbujas' && (
          <VentasMapaMetricaToggle
            value={filtrosAplicados.metrica}
            onChange={handleMetricaChange}
          />
        )}

        {/* Botón filtros */}
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            backgroundColor: DARK.surface,
            border: `1px solid ${DARK.border}`,
            borderRadius: '6px',
            color: DARK.text,
            fontSize: '13px',
            cursor: 'pointer',
            flexShrink: 0,
          }}
          disabled={opcionesLoading}
        >
          <span>⚙</span>
          Filtros
          {countFiltrosActivos(filtrosAplicados) > 0 && (
            <span
              style={{
                backgroundColor: DARK.accentBlue,
                borderRadius: '10px',
                padding: '0 6px',
                fontSize: '10px',
                fontWeight: '700',
              }}
            >
              {countFiltrosActivos(filtrosAplicados)}
            </span>
          )}
        </button>
      </header>

      {/* Mapa — ocupa todo el espacio restante */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <VentasMapa
          data={clientes ?? []}
          metrica={filtrosAplicados.metrica}
          fechaIni={filtrosAplicados.fecha_ini}
          fechaFin={filtrosAplicados.fecha_fin}
          zonas={zonas ?? undefined}
          zonasAgrupacion={
            filtrosAplicados.zonas_agrupacion !== 'OCULTAS'
              ? filtrosAplicados.zonas_agrupacion
              : undefined
          }
          modo={modo}
          calorSubmodo={calorSubmodo}
          dataCompro={dataCompro ?? []}
        />
      </div>

      {/* Cards de zonas — solo cuando hay más de ZONE_BADGE_THRESHOLD zonas */}
      {zonas && zonas.length > ZONE_BADGE_THRESHOLD && (
        <VentasMapaZonasCards zonas={zonas} />
      )}

      {/* Drawer de filtros */}
      <VentasMapaFiltros
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        opciones={opciones}
        filtros={filtrosDraft}
        onChange={(f) => dispatchFiltros({ type: 'SET', filtros: f })}
        onAplicar={handleAplicar}
        onLimpiar={handleLimpiar}
        modoActivo={modo}
        calorSubmodo={calorSubmodo}
        onCalorSubmodoChange={setCalorSubmodo}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper: cuenta filtros activos (para badge del botón)
// ---------------------------------------------------------------------------

function countFiltrosActivos(f: VentasFiltrosState): number {
  let count = 0;
  if (f.canal.length) count++;
  if (f.subcanal.length) count++;
  if (f.localidad.length) count++;
  if (f.lista_precio.length) count++;
  if (f.sucursal_ids.length) count++;
  if (f.genericos.length) count++;
  if (f.marcas.length) count++;
  if (f.fv !== 'AMBAS') count++;
  if (f.rutas.length) count++;
  if (f.preventistas.length) count++;
  if (f.zonas_agrupacion !== 'OCULTAS') count++;
  return count;
}
