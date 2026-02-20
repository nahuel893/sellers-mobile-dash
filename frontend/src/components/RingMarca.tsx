import GaugeSvg from './GaugeSvg';
import { fmtNum, colorByPerformance } from '../lib/format';
import { BRAND_COLORS } from '../lib/constants';

interface RingMarcaProps {
  grupoMarca: string;
  pctTendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
}

export default function RingMarca({
  grupoMarca,
  pctTendencia,
  ventas,
  cupo,
  falta,
}: RingMarcaProps) {
  const brandColor = BRAND_COLORS[grupoMarca] ?? '#6c757d';
  const perfColor = colorByPerformance(pctTendencia);

  return (
    <div className="bg-white rounded-lg shadow-sm p-2.5">
      {/* Header: color dot + nombre */}
      <div className="flex items-center gap-1.5 mb-1">
        <span
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ backgroundColor: brandColor }}
        />
        <span className="text-[11px] xl:text-sm font-bold uppercase text-brand-dark tracking-wider truncate">
          {grupoMarca}
        </span>
      </div>
      {/* Gauge chico */}
      <div className="mx-auto w-[120px]">
        <GaugeSvg
          value={pctTendencia}
          color={perfColor}
          strokeWidth={14}
          fontSize={24}
          className="w-full"
        />
      </div>
      {/* Métricas */}
      <div className="flex gap-1 mt-1 text-center">
        <div className="flex-1">
          <div className="text-[9px] xl:text-xs uppercase text-gray-500">Vendido</div>
          <div className="text-[12px] xl:text-base font-bold text-brand-dark">{fmtNum(ventas)}</div>
        </div>
        <div className="flex-1">
          <div className="text-[9px] xl:text-xs uppercase text-gray-500">Cupo</div>
          <div className="text-[12px] xl:text-base font-bold text-brand-dark">{fmtNum(cupo)}</div>
        </div>
        <div className="flex-1">
          <div className="text-[9px] xl:text-xs uppercase text-gray-500">Falta</div>
          <div className="text-[12px] xl:text-base font-bold text-perf-red">{fmtNum(falta)}</div>
        </div>
      </div>
    </div>
  );
}
