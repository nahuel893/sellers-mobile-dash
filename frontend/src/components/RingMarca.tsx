import GaugeSvg from './GaugeSvg';
import { fmtNum, colorByPerformance } from '../lib/format';
import { BRAND_COLORS } from '../lib/constants';

interface RingMarcaProps {
  grupoMarca: string;
  pctTendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
  diasRestantes?: number;
}

export default function RingMarca({
  grupoMarca,
  pctTendencia,
  ventas,
  cupo,
  falta,
  diasRestantes,
}: RingMarcaProps) {
  const brandColor = BRAND_COLORS[grupoMarca] ?? '#6c757d';
  const perfColor = colorByPerformance(pctTendencia);
  const vtaDiaria = diasRestantes && diasRestantes > 0 && falta > 0
    ? Math.ceil(falta / diasRestantes)
    : 0;

  return (
    <div className="bg-bg-1 border border-line rounded-xl p-3">
      {/* Header: color dot + nombre */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className="w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: brandColor }}
        />
        <span className="text-xs xl:text-base font-bold uppercase text-ink-0 tracking-wider truncate">
          {grupoMarca}
        </span>
      </div>
      {/* Gauge chico */}
      <div className="mx-auto w-[140px]">
        <GaugeSvg
          value={pctTendencia}
          color={perfColor}
          strokeWidth={14}
          fontSize={28}
          className="w-full"
        />
      </div>
      {/* Métricas */}
      <div className="flex mt-2 text-center divide-x divide-line">
        <div className="flex-1 px-1">
          <div className="text-[10px] xl:text-sm uppercase text-ink-2">Vendido</div>
          <div className="text-base xl:text-xl font-mono font-bold text-ink-0">{fmtNum(ventas)}</div>
        </div>
        <div className="flex-1 px-1">
          <div className="text-[10px] xl:text-sm uppercase text-ink-2">Cupo</div>
          <div className="text-base xl:text-xl font-mono font-bold text-ink-0">{fmtNum(cupo)}</div>
        </div>
        <div className="flex-1 px-1">
          <div className="text-[10px] xl:text-sm uppercase text-ink-2">Falta</div>
          <div className="text-base xl:text-xl font-mono font-bold text-danger">{fmtNum(falta)}</div>
        </div>
      </div>
      {vtaDiaria > 0 && (
        <div className="mt-2 text-center">
          <div className="text-[10px] xl:text-sm uppercase text-ink-2">Vta/Día</div>
          <div className="text-base xl:text-xl font-mono font-bold text-warn">{fmtNum(vtaDiaria)}</div>
        </div>
      )}
    </div>
  );
}
