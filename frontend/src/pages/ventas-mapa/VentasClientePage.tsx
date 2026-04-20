/**
 * VentasClientePage — detalle completo de un cliente.
 *
 * Ruta: /ventas/cliente/:id
 *
 * Layout:
 *   Header (info + nav) → KPIs (3 cards) → Tabla jerárquica 12 meses
 *
 * Tema oscuro, full-height, scroll en la tabla.
 */
import { useParams } from 'react-router';
import { useVentasClienteDetalle } from '../../hooks/ventas-mapa/use-ventas-cliente-detalle';
import VentasClienteHeader from '../../components/ventas-mapa/VentasClienteHeader';
import VentasClienteKpis from '../../components/ventas-mapa/VentasClienteKpis';
import VentasClienteTabla from '../../components/ventas-mapa/VentasClienteTabla';
import { DARK } from '../../lib/ventas-constants';

export default function VentasClientePage() {
  const { id } = useParams<{ id: string }>();
  const idCliente = id ? parseInt(id, 10) : null;

  const { data, isLoading, isError, error } = useVentasClienteDetalle(idCliente);

  // ---------------------------------------------------------------------------
  // Estado: cargando
  // ---------------------------------------------------------------------------
  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          height: '100vh',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: DARK.bg,
          color: DARK.textSecondary,
          fontSize: '15px',
        }}
      >
        Cargando cliente…
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Estado: error / no encontrado
  // ---------------------------------------------------------------------------
  if (isError || !data) {
    const msg =
      error instanceof Error
        ? error.message.includes('404')
          ? 'Cliente no encontrado'
          : error.message.includes('403')
            ? 'No tenés acceso a este cliente'
            : 'Error al cargar el cliente'
        : 'Error al cargar el cliente';

    return (
      <div
        style={{
          display: 'flex',
          height: '100vh',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          backgroundColor: DARK.bg,
          color: DARK.textSecondary,
        }}
      >
        <span style={{ fontSize: '32px' }}>⚠</span>
        <span style={{ fontSize: '15px' }}>{msg}</span>
        <a
          href="/ventas"
          style={{ fontSize: '13px', color: DARK.accentBlue, textDecoration: 'none' }}
        >
          ← Volver al mapa
        </a>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render principal
  // ---------------------------------------------------------------------------
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
      <VentasClienteHeader info={data.info} />
      <VentasClienteKpis kpis={data.kpis} />
      <VentasClienteTabla tabla={data.tabla} />
    </div>
  );
}
