import GaugeSvg from './GaugeSvg';
import { fmtNum, colorByPerformance } from '../lib/format';

interface GaugeTotalProps {
  pctTendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
  tendencia: number;
  title?: string;
}

export default function GaugeTotal({
  pctTendencia,
  ventas,
  cupo,
  falta,
  tendencia,
  title,
}: GaugeTotalProps) {
  const color = colorByPerformance(pctTendencia);

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 xl:flex xl:items-center xl:gap-6 xl:p-5">
      {title && (
        <h3 className="text-sm font-bold text-brand-dark uppercase tracking-wider mb-2 xl:hidden">
          {title}
        </h3>
      )}
      <div className="mx-auto w-[200px] xl:w-[280px] xl:flex-shrink-0">
        <GaugeSvg
          value={pctTendencia}
          color={color}
          fontSize={42}
          className="w-full"
        />
      </div>
      <div className="flex gap-2 mt-2 xl:mt-0 xl:flex-1 xl:flex-wrap">
        <MetricBox label="Vendido" value={fmtNum(ventas)} />
        <MetricBox label="Cupo" value={fmtNum(cupo)} />
        <MetricBox label="Falta" value={fmtNum(falta)} className="text-perf-red" />
        <MetricBox label="Tendencia" value={fmtNum(tendencia)} />
      </div>
    </div>
  );
}

function MetricBox({
  label,
  value,
  className = '',
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="flex-1 min-w-[60px] text-center">
      <div className="text-[10px] xl:text-sm uppercase tracking-wider text-gray-500 font-medium">
        {label}
      </div>
      <div className={`text-sm xl:text-xl font-bold text-brand-dark ${className}`}>
        {value}
      </div>
    </div>
  );
}
