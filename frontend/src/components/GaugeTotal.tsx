import GaugeSvg from './GaugeSvg';
import { fmtNum, colorByPerformance } from '../lib/format';

interface GaugeTotalProps {
  pctTendencia: number;
  ventas: number;
  cupo: number;
  falta: number;
  tendencia: number;
  diasRestantes?: number;
  title?: string;
}

export default function GaugeTotal({
  pctTendencia,
  ventas,
  cupo,
  falta,
  tendencia,
  diasRestantes,
}: GaugeTotalProps) {
  const color = colorByPerformance(pctTendencia);
  const vtaDiaria = diasRestantes && diasRestantes > 0 && falta > 0
    ? Math.ceil(falta / diasRestantes)
    : 0;

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 xl:flex xl:items-center xl:gap-8 xl:p-6">
      <div className="mx-auto w-[260px] xl:w-[240px] xl:flex-shrink-0">
        <GaugeSvg
          value={pctTendencia}
          color={color}
          fontSize={42}
          className="w-full"
        />
      </div>
      <div className="flex flex-wrap gap-3 mt-3 xl:mt-0 xl:flex-1">
        <MetricBox label="Vendido" value={fmtNum(ventas)} />
        <MetricBox label="Cupo" value={fmtNum(cupo)} />
        <MetricBox label="Falta" value={fmtNum(falta)} className="text-perf-red" />
        <MetricBox label="Tendencia" value={fmtNum(tendencia)} />
        {vtaDiaria > 0 && (
          <MetricBox label="Vta/Día" value={fmtNum(vtaDiaria)} className="text-orange-500" />
        )}
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
    <div className="flex-1 min-w-[70px] text-center">
      <div className="text-xs xl:text-base uppercase tracking-wider text-gray-500 font-medium">
        {label}
      </div>
      <div className={`text-2xl xl:text-4xl font-bold text-brand-dark ${className}`}>
        {value}
      </div>
    </div>
  );
}
