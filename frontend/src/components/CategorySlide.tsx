import type { CategoryData } from '../types/api';
import type { CategoryKey } from '../lib/constants';
import { BRAND_ORDER, CATEGORY_NAMES } from '../lib/constants';
import GaugeTotal from './GaugeTotal';
import RingMarca from './RingMarca';

interface CategorySlideProps {
  categoryKey: CategoryKey;
  data: CategoryData;
}

export default function CategorySlide({ categoryKey, data }: CategorySlideProps) {
  const { resumen, datos } = data;
  const title = `Total ${CATEGORY_NAMES[categoryKey]}`;

  // Para CERVEZAS: mostrar desglose por marca en orden
  const brandCards =
    categoryKey === 'CERVEZAS'
      ? BRAND_ORDER.map((brand) => datos.find((d) => d.grupo_marca === brand)).filter(Boolean)
      : [];

  return (
    <div className="px-2 py-3">
      <GaugeTotal
        title={title}
        pctTendencia={resumen.pct_tendencia}
        ventas={resumen.ventas}
        cupo={resumen.cupo}
        falta={resumen.falta}
        tendencia={resumen.tendencia}
      />

      {brandCards.length > 0 && (
        <>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mt-4 mb-2 px-1">
            Detalle por Marca
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
            {brandCards.map((d) => (
              <RingMarca
                key={d!.grupo_marca}
                grupoMarca={d!.grupo_marca!}
                pctTendencia={d!.pct_tendencia}
                ventas={d!.ventas}
                cupo={d!.cupo}
                falta={d!.falta}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
