import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router';
import Header from '../components/Header';
import CategorySlide from '../components/CategorySlide';
import CoberturaSection from '../components/CoberturaSection';
import { useSucursales } from '../hooks/use-sucursales';
import { useSupervisores } from '../hooks/use-supervisores';
import { useDashboard } from '../hooks/use-dashboard';
import { useCobertura } from '../hooks/use-cobertura';
import { CATEGORIES, CATEGORY_NAMES, type CategoryKey } from '../lib/constants';
import type { VendedorListItem } from '../types/api';

const DEFAULT_INTERVAL = 10;

export default function PaneoPage() {
  const [params] = useSearchParams();
  const interval = (parseInt(params.get('intervalo') ?? '', 10) || DEFAULT_INTERVAL) * 1000;

  const [sucursal, setSucursal] = useState<string | null>(null);
  const [supIdx, setSupIdx] = useState(0);
  const [step, setStep] = useState<'supervisor' | 'vendedor'>('supervisor');
  const [vendIdx, setVendIdx] = useState(0);

  const { data: sucursales } = useSucursales();
  const { data: supervisores } = useSupervisores(sucursal);

  const currentSup = supervisores?.[supIdx] ?? null;
  const { data: dashboard } = useDashboard(currentSup, sucursal);
  const { data: cobertura } = useCobertura(sucursal ?? undefined, currentSup ?? undefined);

  // Auto-select first sucursal
  useEffect(() => {
    if (sucursales?.length && !sucursal) {
      setSucursal(sucursales[0]);
    }
  }, [sucursales, sucursal]);

  const vendedores = dashboard?.vendedores ?? [];
  const currentVend = step === 'vendedor' ? vendedores[vendIdx] : null;

  const advance = useCallback(() => {
    if (!supervisores?.length) return;

    if (step === 'supervisor') {
      // Move to first vendor of this supervisor
      if (vendedores.length > 0) {
        setStep('vendedor');
        setVendIdx(0);
      } else {
        // No vendors, skip to next supervisor
        const nextSup = (supIdx + 1) % supervisores.length;
        setSupIdx(nextSup);
      }
    } else {
      // Next vendor
      const nextVend = vendIdx + 1;
      if (nextVend < vendedores.length) {
        setVendIdx(nextVend);
      } else {
        // Move to next supervisor
        const nextSup = (supIdx + 1) % supervisores.length;
        setSupIdx(nextSup);
        setStep('supervisor');
        setVendIdx(0);
      }
    }
  }, [step, supIdx, vendIdx, supervisores, vendedores]);

  // Auto-advance timer
  useEffect(() => {
    if (!dashboard) return;
    const timer = setInterval(advance, interval);
    return () => clearInterval(timer);
  }, [advance, interval, dashboard]);

  // Progress info
  const totalSteps = supervisores
    ? supervisores.length + vendedores.length
    : 0;
  const currentStep = step === 'supervisor' ? 1 : vendIdx + 2;

  return (
    <div className="min-h-screen">
      <Header />

      {/* Progress bar */}
      <div className="px-3 py-2 flex items-center gap-3">
        <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-dark rounded-full transition-all duration-500"
            style={{ width: totalSteps ? `${(currentStep / totalSteps) * 100}%` : '0%' }}
          />
        </div>
        <span className="text-xs text-gray-400 font-medium whitespace-nowrap">
          {currentSup} {step === 'vendedor' && currentVend ? `· ${currentVend.nombre}` : ''}
        </span>
      </div>

      {step === 'supervisor' && dashboard && (
        <SupervisorView
          nombre={currentSup ?? ''}
          dashboard={dashboard}
          cobertura={cobertura}
        />
      )}

      {step === 'vendedor' && currentVend && dashboard && (
        <VendedorView
          vendedor={currentVend}
          dashboard={dashboard}
          cobertura={cobertura}
        />
      )}
    </div>
  );
}

/* --- Supervisor view --- */

function SupervisorView({
  nombre,
  dashboard,
  cobertura,
}: {
  nombre: string;
  dashboard: { supervisor: Record<string, { resumen: any; datos: any[] }> };
  cobertura: any;
}) {
  return (
    <div className="px-2">
      <h1 className="text-lg font-extrabold text-brand-dark px-1 pb-2">
        Supervisor: {nombre}
      </h1>

      {CATEGORIES.map((key) => {
        const catData = dashboard.supervisor[key];
        if (!catData) return null;
        return (
          <div key={key} className="border-t border-gray-200 mt-2">
            <CategorySlide categoryKey={key as CategoryKey} data={catData} />
          </div>
        );
      })}

      {cobertura && cobertura.vendedores?.length > 0 && (
        <CoberturaSection vendedores={cobertura.vendedores} />
      )}
    </div>
  );
}

/* --- Vendedor view --- */

function VendedorView({
  vendedor,
  dashboard,
  cobertura,
}: {
  vendedor: VendedorListItem;
  dashboard: any;
  cobertura: any;
}) {
  const pct = vendedor.categories?.CERVEZAS?.resumen.pct_tendencia ?? 0;

  // Find this vendor's cobertura
  const cobVendedor = cobertura?.vendedores?.find(
    (v: any) => v.vendedor === vendedor.nombre,
  );

  return (
    <div className="px-2">
      <div className="flex items-baseline gap-2 px-1 pb-2">
        <h1 className="text-lg font-extrabold text-brand-dark">{vendedor.nombre}</h1>
        <span className="text-xs text-gray-400 font-medium">{pct.toFixed(1)}%</span>
      </div>

      {CATEGORIES.map((key) => {
        const catData = vendedor.categories?.[key];
        if (!catData) return null;
        return (
          <div key={key} className="border-t border-gray-200 mt-2">
            <CategorySlide categoryKey={key as CategoryKey} data={catData} />
          </div>
        );
      })}

      {cobVendedor && cobVendedor.marcas?.length > 0 && (
        <CoberturaSection vendedores={[cobVendedor]} />
      )}
    </div>
  );
}
