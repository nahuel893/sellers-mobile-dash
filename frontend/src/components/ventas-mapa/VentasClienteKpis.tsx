/**
 * VentasClienteKpis — tres cards de KPIs del mes actual.
 * Bultos | Facturación | Documentos
 * Tema oscuro.
 */
import type { VentasClienteKPIs } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasClienteKpisProps {
  kpis: VentasClienteKPIs;
}

function formatNumber(n: number, decimals = 0): string {
  return n.toLocaleString('es-AR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatCurrency(n: number): string {
  if (n >= 1_000_000) {
    return `$${(n / 1_000_000).toLocaleString('es-AR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`;
  }
  if (n >= 1_000) {
    return `$${(n / 1_000).toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}K`;
  }
  return `$${formatNumber(n, 0)}`;
}

interface KpiCardProps {
  label: string;
  value: string;
  accent?: string;
}

function KpiCard({ label, value, accent }: KpiCardProps) {
  return (
    <div
      style={{
        backgroundColor: DARK.card,
        border: `1px solid ${DARK.border}`,
        borderRadius: '10px',
        padding: '16px 20px',
        flex: '1',
        minWidth: '140px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      <span
        style={{
          fontSize: '11px',
          color: DARK.textMuted,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: '26px',
          fontWeight: '700',
          color: accent ?? DARK.text,
          lineHeight: 1,
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function VentasClienteKpis({ kpis }: VentasClienteKpisProps) {
  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        padding: '16px 24px',
        flexWrap: 'wrap',
        flexShrink: 0,
        backgroundColor: DARK.bg,
        borderBottom: `1px solid ${DARK.border}`,
      }}
    >
      <KpiCard
        label="Bultos del mes"
        value={formatNumber(kpis.bultos_mes)}
        accent={DARK.accentBlue}
      />
      <KpiCard
        label="Facturación del mes"
        value={formatCurrency(kpis.facturacion_mes)}
        accent={DARK.accentGreen}
      />
      <KpiCard
        label="Documentos del mes"
        value={formatNumber(kpis.documentos_mes)}
      />
    </div>
  );
}
