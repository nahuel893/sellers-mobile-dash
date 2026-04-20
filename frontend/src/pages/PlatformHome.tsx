import { useDiasHabiles } from '../hooks/use-dias-habiles';
import { useAuth } from '../hooks/use-auth';
import { formatDateSpanish } from '../lib/format';
import DashboardCard from '../components/DashboardCard';
import type { DashboardCardDef } from '../components/DashboardCard';

/** Cards visibles en la plataforma. allowedRoles=undefined → todos los roles autenticados. */
const PLATFORM_CARDS: DashboardCardDef[] = [
  {
    id: 'sellers',
    title: 'Vendedores',
    description: 'Avance de preventa por vendedor, supervisor y sucursal.',
    href: '/sellers',
    icon: '📊',
    allowedRoles: undefined,
  },
  {
    id: 'admin',
    title: 'Administración',
    description: 'Gestión de usuarios, roles y permisos de la plataforma.',
    href: '/admin/usuarios',
    icon: '⚙️',
    allowedRoles: ['admin'],
  },
];

export default function PlatformHome() {
  const { data } = useDiasHabiles();
  const { user, logout } = useAuth();

  const visibleCards = PLATFORM_CARDS.filter((card) => {
    if (!card.allowedRoles) return true;
    return user?.role ? card.allowedRoles.includes(user.role) : false;
  });

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-gradient-to-br from-brand-dark to-brand-dark2 text-white px-4 pt-5 pb-4 rounded-b-[20px] xl:flex xl:items-center xl:justify-between xl:px-8">
        <div className="xl:flex xl:items-baseline xl:gap-4">
          <div className="flex items-baseline justify-between">
            <h1 className="text-lg font-extrabold tracking-tight">Plataforma Preventa</h1>
            {user && (
              <button
                onClick={logout}
                className="text-xs text-white/60 hover:text-white underline ml-4 xl:hidden"
                type="button"
              >
                Salir
              </button>
            )}
          </div>
          {data && (
            <p className="text-xs text-white/60 mt-0.5 xl:mt-0">
              {formatDateSpanish(data.fecha)}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3 mt-3 xl:mt-0">
          {data && (
            <div className="flex gap-2 flex-1 xl:flex-none">
              <DayBox label="Días hábiles" value={data.habiles} />
              <DayBox label="Transcurridos" value={data.transcurridos} colorClass="text-[#64B5F6]" />
              <DayBox label="Faltan" value={data.restantes} colorClass="text-[#FFC107]" />
            </div>
          )}
          {user && (
            <button
              onClick={logout}
              className="hidden xl:block text-xs text-white/60 hover:text-white underline whitespace-nowrap"
              type="button"
            >
              Cerrar sesión
            </button>
          )}
        </div>
      </header>

      {/* User greeting */}
      {user && (
        <div className="px-4 pt-5 pb-2">
          <p className="text-sm text-gray-500">
            Hola, <span className="font-semibold text-brand-dark">{user.nombre_completo || user.username}</span>
          </p>
        </div>
      )}

      {/* Cards */}
      <div className="px-4 pt-3 pb-8 flex flex-col gap-3">
        {visibleCards.map((card) => (
          <DashboardCard key={card.id} card={card} />
        ))}
      </div>
    </div>
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
