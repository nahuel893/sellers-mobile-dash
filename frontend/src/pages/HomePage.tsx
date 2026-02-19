import { useState } from 'react';
import Header from '../components/Header';
import Filters from '../components/Filters';
import CategoryToggle from '../components/CategoryToggle';
import VendorIndex from '../components/VendorIndex';
import SummaryBlock from '../components/SummaryBlock';
import VendorBlock from '../components/VendorBlock';
import { useSucursales } from '../hooks/use-sucursales';
import { useSupervisores } from '../hooks/use-supervisores';
import { useDashboard } from '../hooks/use-dashboard';

export default function HomePage() {
  const [sucursal, setSucursal] = useState<string | null>(null);
  const [supervisor, setSupervisor] = useState<string | null>(null);
  const [globalSlide, setGlobalSlide] = useState(0);

  const { data: sucursales } = useSucursales();
  const { data: supervisores, isLoading: isLoadingSupervisores } = useSupervisores(sucursal);
  const { data: dashboard, isLoading: isLoadingDashboard } = useDashboard(supervisor, sucursal);

  function handleSucursalChange(value: string) {
    setSucursal(value);
    setSupervisor(null);
  }

  function handleSupervisorChange(value: string) {
    setSupervisor(value);
  }

  // Auto-select first sucursal when list loads
  if (sucursales?.length && !sucursal) {
    setSucursal(sucursales[0]);
  }

  // Auto-select first supervisor when list loads
  if (supervisores?.length && !supervisor) {
    setSupervisor(supervisores[0]);
  }

  const sucursalPct = dashboard
    ? dashboard.sucursal.CERVEZAS?.resumen.pct_tendencia ?? 0
    : 0;
  const supervisorPct = dashboard
    ? dashboard.supervisor.CERVEZAS?.resumen.pct_tendencia ?? 0
    : 0;

  return (
    <>
      <Header />

      <Filters
        sucursales={sucursales ?? []}
        selectedSucursal={sucursal}
        onSucursalChange={handleSucursalChange}
        supervisores={supervisores ?? []}
        selectedSupervisor={supervisor}
        onSupervisorChange={handleSupervisorChange}
        isLoadingSupervisores={isLoadingSupervisores}
      />

      <CategoryToggle activeIndex={globalSlide} onChange={setGlobalSlide} />

      {isLoadingDashboard && (
        <p className="text-center text-sm text-gray-400 py-8">Cargando datos...</p>
      )}

      {dashboard && (
        <>
          <SummaryBlock
            title={sucursal ?? 'Sucursal'}
            pctTendencia={sucursalPct}
            categories={dashboard.sucursal}
            variant="sucursal"
            globalSlideIndex={globalSlide}
          />

          <SummaryBlock
            title={supervisor ?? 'Supervisor'}
            pctTendencia={supervisorPct}
            categories={dashboard.supervisor}
            variant="supervisor"
            globalSlideIndex={globalSlide}
          />

          <VendorIndex vendedores={dashboard.vendedores} />

          {dashboard.vendedores.map((v) => (
            <VendorBlock
              key={v.slug}
              vendedor={v}
              globalSlideIndex={globalSlide}
            />
          ))}
        </>
      )}
    </>
  );
}
