/**
 * VentasClienteHeader — cabecera de la página de detalle de cliente.
 * Muestra: fantasia (grande), razon_social + id_cliente, metadata.
 * Tema oscuro.
 */
import { Link } from 'react-router';
import type { VentasClienteInfo } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasClienteHeaderProps {
  info: VentasClienteInfo;
}

const LABEL_STYLE: React.CSSProperties = {
  fontSize: '11px',
  color: DARK.textMuted,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const VALUE_STYLE: React.CSSProperties = {
  fontSize: '13px',
  color: DARK.textSecondary,
};

function MetaItem({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === '') return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <span style={LABEL_STYLE}>{label}</span>
      <span style={VALUE_STYLE}>{value}</span>
    </div>
  );
}

export default function VentasClienteHeader({ info }: VentasClienteHeaderProps) {
  const nombre = info.fantasia || info.razon_social;
  const subtitulo = info.fantasia ? info.razon_social : null;

  return (
    <header
      style={{
        backgroundColor: DARK.card,
        borderBottom: `1px solid ${DARK.border}`,
        padding: '16px 24px',
        flexShrink: 0,
      }}
    >
      {/* Nav: volver al mapa */}
      <div style={{ marginBottom: '12px' }}>
        <Link
          to="/ventas"
          style={{
            fontSize: '13px',
            color: DARK.accentBlue,
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          ← Volver al mapa
        </Link>
      </div>

      {/* Nombre principal */}
      <h1
        style={{
          fontSize: '22px',
          fontWeight: '700',
          color: DARK.text,
          margin: 0,
          lineHeight: 1.2,
        }}
      >
        {nombre}
      </h1>

      {/* Subtítulo + ID */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginTop: '4px',
          flexWrap: 'wrap',
        }}
      >
        {subtitulo && (
          <span style={{ fontSize: '14px', color: DARK.textSecondary }}>
            {subtitulo}
          </span>
        )}
        <span
          style={{
            fontSize: '12px',
            color: DARK.textMuted,
            backgroundColor: DARK.surface,
            padding: '2px 8px',
            borderRadius: '4px',
            fontFamily: 'monospace',
          }}
        >
          #{info.id_cliente}
        </span>
      </div>

      {/* Metadata grid */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '20px',
          marginTop: '14px',
        }}
      >
        <MetaItem label="Localidad" value={info.localidad} />
        <MetaItem label="Canal" value={info.canal} />
        <MetaItem label="Sucursal" value={info.sucursal} />
        <MetaItem label="Preventista" value={info.preventista_fv1} />
        <MetaItem label="Ruta" value={info.ruta_fv1} />
        <MetaItem label="Lista de precio" value={info.lista_precio} />
      </div>
    </header>
  );
}
