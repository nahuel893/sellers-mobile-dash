/**
 * Segmented control para seleccionar la métrica del mapa (Bultos / Facturación / Documentos).
 */
import type { VentasMetrica } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

const OPCIONES: { value: VentasMetrica; label: string }[] = [
  { value: 'bultos', label: 'Bultos' },
  { value: 'facturacion', label: 'Facturación' },
  { value: 'documentos', label: 'Documentos' },
];

interface VentasMapaMetricaToggleProps {
  value: VentasMetrica;
  onChange: (metrica: VentasMetrica) => void;
}

export default function VentasMapaMetricaToggle({
  value,
  onChange,
}: VentasMapaMetricaToggleProps) {
  return (
    <div
      style={{
        display: 'flex',
        backgroundColor: DARK.surface,
        border: `1px solid ${DARK.border}`,
        borderRadius: '6px',
        overflow: 'hidden',
      }}
    >
      {OPCIONES.map((op, idx) => {
        const isActive = op.value === value;
        return (
          <button
            key={op.value}
            type="button"
            onClick={() => onChange(op.value)}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: isActive ? '700' : '400',
              color: isActive ? '#fff' : DARK.textSecondary,
              backgroundColor: isActive ? DARK.accentBlue : 'transparent',
              border: 'none',
              borderLeft: idx > 0 ? `1px solid ${DARK.border}` : 'none',
              cursor: 'pointer',
              transition: 'background-color 0.15s, color 0.15s',
              whiteSpace: 'nowrap',
            }}
          >
            {op.label}
          </button>
        );
      })}
    </div>
  );
}
