import { useState } from 'react';
import { colorByPerformance } from '../lib/format';
import type { CoberturaVendedorData } from '../types/api';

interface CoberturaSectionProps {
  vendedores: CoberturaVendedorData[];
}

export default function CoberturaSection({ vendedores }: CoberturaSectionProps) {
  const [expandedVendor, setExpandedVendor] = useState<string | null>(null);

  const sorted = [...vendedores].sort((a, b) => a.vendedor.localeCompare(b.vendedor));

  return (
    <div className="mx-2 mt-4 mb-4">
      <h2 className="text-sm font-bold text-brand-dark uppercase tracking-wider px-1 mb-2">
        Cobertura
      </h2>

      {sorted.map((v) => {
        const expanded = expandedVendor === v.vendedor;
        const marcas = [...v.marcas].sort((a, b) => b.cupo - a.cupo);

        return (
          <div key={v.vendedor} className="bg-white rounded-xl shadow-sm mb-2 overflow-hidden">
            <button
              type="button"
              className="w-full flex items-center justify-between px-3 py-3 text-left"
              onClick={() => setExpandedVendor(expanded ? null : v.vendedor)}
            >
              <h3 className="text-sm font-bold text-brand-dark truncate">{v.vendedor}</h3>
              <span
                className="text-gray-400 text-lg transition-transform ml-2"
                style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
              >
                &#9662;
              </span>
            </button>

            {expanded && (
              <div className="border-t border-gray-100 px-2 pb-3 pt-1 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-[10px] uppercase text-gray-500 tracking-wider">
                      <th className="text-left py-1 px-1 font-medium">Marca</th>
                      <th className="text-right py-1 px-1 font-medium">Real</th>
                      <th className="text-right py-1 px-1 font-medium">Cupo</th>
                      <th className="text-right py-1 px-1 font-medium">Falta</th>
                      <th className="text-right py-1 px-1 font-medium">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marcas.map((m, i) => {
                      const falta = Math.max(m.cupo - m.cobertura, 0);
                      const color = colorByPerformance(m.pct_cobertura);
                      const prevGenerico = i > 0 ? marcas[i - 1].generico : null;
                      const showHeader = m.generico !== prevGenerico;
                      return (
                        <>
                          {showHeader && (
                            <tr key={`hdr-${m.generico}`} className="bg-gray-50">
                              <td colSpan={5} className="py-1.5 px-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                                {m.generico}
                              </td>
                            </tr>
                          )}
                          <tr key={m.marca} className="border-t border-gray-50">
                            <td className="py-1.5 px-1 pl-3 font-semibold text-brand-dark text-xs">{m.marca}</td>
                            <td className="py-1.5 px-1 text-right font-bold" style={{ color }}>{m.cobertura}</td>
                            <td className="py-1.5 px-1 text-right font-bold text-brand-dark">{m.cupo}</td>
                            <td className="py-1.5 px-1 text-right font-bold text-red-500">{falta > 0 ? `-${falta}` : '—'}</td>
                            <td className="py-1.5 px-1 text-right font-bold" style={{ color }}>{m.pct_cobertura.toFixed(0)}%</td>
                          </tr>
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
