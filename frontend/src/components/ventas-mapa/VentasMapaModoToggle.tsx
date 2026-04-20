/**
 * Segmented control para seleccionar el modo de visualización del mapa.
 * Tres opciones: Burbujas / Calor / Compro
 */
import type { VentasMapaModo } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasMapaModoToggleProps {
  value: VentasMapaModo;
  onChange: (modo: VentasMapaModo) => void;
}

const MODOS: { value: VentasMapaModo; label: string }[] = [
  { value: 'burbujas', label: 'Burbujas' },
  { value: 'calor', label: 'Calor' },
  { value: 'compro', label: 'Compro' },
];

export default function VentasMapaModoToggle({
  value,
  onChange,
}: VentasMapaModoToggleProps) {
  return (
    <div
      style={{
        display: 'flex',
        backgroundColor: DARK.surface,
        border: `1px solid ${DARK.border}`,
        borderRadius: '6px',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {MODOS.map((modo, idx) => {
        const isActive = value === modo.value;
        return (
          <button
            key={modo.value}
            type="button"
            onClick={() => onChange(modo.value)}
            style={{
              padding: '6px 12px',
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
            {modo.label}
          </button>
        );
      })}
    </div>
  );
}
