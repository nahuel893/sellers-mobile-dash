import { useDiasHabiles } from '../hooks/use-dias-habiles';
import { useAuth } from '../hooks/use-auth';
import { formatDateSpanish } from '../lib/format';

export default function Header() {
  const { data } = useDiasHabiles();
  const { user, logout } = useAuth();

  return (
    <header
      id="top"
      className="bg-bg-1 border-b border-line text-ink-0 px-4 pt-5 pb-4 rounded-b-[20px] xl:flex xl:items-center xl:justify-between xl:px-8"
    >
      <div className="xl:flex xl:items-baseline xl:gap-4">
        <div className="flex items-baseline justify-between">
          <h1 className="text-lg font-extrabold tracking-tight">Avance Preventa</h1>
          {user && (
            <button
              onClick={logout}
              className="text-xs text-ink-2 hover:text-ink-0 underline ml-4 xl:hidden"
              type="button"
            >
              Salir
            </button>
          )}
        </div>
        {data && (
          <p className="text-xs text-ink-2 mt-0.5 xl:mt-0">
            {formatDateSpanish(data.fecha)}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3 mt-3 xl:mt-0">
        {data && (
          <div className="flex gap-2 flex-1 xl:flex-none">
            <DayBox label="Días hábiles" value={data.habiles} />
            <DayBox label="Transcurridos" value={data.transcurridos} colorClass="text-info" />
            <DayBox label="Faltan" value={data.restantes} colorClass="text-warn" />
          </div>
        )}
        {user && (
          <button
            onClick={logout}
            className="hidden xl:block text-xs text-ink-2 hover:text-ink-0 underline whitespace-nowrap"
            type="button"
          >
            Cerrar sesión
          </button>
        )}
      </div>
    </header>
  );
}

function DayBox({
  label,
  value,
  colorClass = 'text-ink-0',
}: {
  label: string;
  value: number;
  colorClass?: string;
}) {
  return (
    <div className="flex-1 bg-bg-2 border border-line rounded-[10px] py-2 px-2.5 text-center">
      <div className="text-[10px] uppercase tracking-wider text-ink-2 font-medium">
        {label}
      </div>
      <div className={`text-xl font-mono font-bold ${colorClass}`}>{value}</div>
    </div>
  );
}
