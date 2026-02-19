import { useDiasHabiles } from '../hooks/use-dias-habiles';
import { formatDateSpanish } from '../lib/format';

export default function Header() {
  const { data } = useDiasHabiles();

  return (
    <header
      id="top"
      className="bg-gradient-to-br from-brand-dark to-brand-dark2 text-white px-4 pt-5 pb-4 rounded-b-[20px] xl:flex xl:items-center xl:justify-between xl:px-8"
    >
      <div className="xl:flex xl:items-baseline xl:gap-4">
        <h1 className="text-lg font-extrabold tracking-tight">Avance Preventa</h1>
        {data && (
          <p className="text-xs text-white/60 mt-0.5 xl:mt-0">
            {formatDateSpanish(data.fecha)}
          </p>
        )}
      </div>

      {data && (
        <div className="flex gap-2 mt-3 xl:mt-0">
          <DayBox label="Días hábiles" value={data.habiles} />
          <DayBox label="Transcurridos" value={data.transcurridos} colorClass="text-[#64B5F6]" />
          <DayBox label="Faltan" value={data.restantes} colorClass="text-[#FFC107]" />
        </div>
      )}
    </header>
  );
}

function DayBox({
  label,
  value,
  colorClass = 'text-white',
}: {
  label: string;
  value: number;
  colorClass?: string;
}) {
  return (
    <div className="flex-1 bg-white/10 rounded-[10px] py-2 px-2.5 text-center">
      <div className="text-[10px] uppercase tracking-wider text-white/50 font-medium">
        {label}
      </div>
      <div className={`text-xl font-bold ${colorClass}`}>{value}</div>
    </div>
  );
}
