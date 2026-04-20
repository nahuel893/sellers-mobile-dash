/**
 * VentasClienteTabla — tabla jerárquica de ventas por mes (12 meses).
 *
 * Estructura de filas (identificada por strings vacíos):
 *   - Genérico:  marca === '' && articulo === ''  → fondo oscuro, bold
 *   - Marca:     articulo === ''  (marca !== '')  → fondo intermedio, semibold
 *   - Artículo:  ninguno vacío                   → normal; sin ventas → gris
 *
 * Incluye:
 *   - Encabezado sticky con los 12 meses
 *   - Jump-to: dropdowns para navegar al genérico o marca
 *   - Scroll horizontal si el viewport es angosto
 *
 * Tema oscuro.
 */
import { useRef } from 'react';
import type { VentasClienteTabla as TablaRow } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasClienteTablaProps {
  tabla: TablaRow[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isGenerico(row: TablaRow): boolean {
  return row.marca === '' && row.articulo === '';
}

function isMarca(row: TablaRow): boolean {
  return row.articulo === '' && row.marca !== '';
}

function hasSales(row: TablaRow): boolean {
  return row.total > 0;
}

function getMeses(row: TablaRow): string[] {
  return Object.keys(row.meses).sort();
}

function formatVal(v: number): string {
  if (v === 0) return '–';
  return v.toLocaleString('es-AR', { maximumFractionDigits: 0 });
}

function formatHeader(yyyyMM: string): string {
  const [year, month] = yyyyMM.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  const mes = date.toLocaleString('es-AR', { month: 'short' });
  const anio = year.slice(2);
  return `${mes.charAt(0).toUpperCase()}${mes.slice(1)} ${anio}`;
}

// ---------------------------------------------------------------------------
// Jump-to dropdowns
// ---------------------------------------------------------------------------

function JumpToDropdowns({ tabla }: { tabla: TablaRow[] }) {
  const genericos = [...new Set(tabla.filter(isGenerico).map((r) => r.generico))];
  const marcas = [...new Set(tabla.filter(isMarca).map((r) => r.marca))];

  function scrollTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  if (genericos.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        padding: '12px 24px',
        backgroundColor: DARK.bg,
        borderBottom: `1px solid ${DARK.border}`,
        flexShrink: 0,
        flexWrap: 'wrap',
        alignItems: 'center',
      }}
    >
      <span style={{ fontSize: '12px', color: DARK.textMuted }}>Ir a:</span>

      {genericos.length > 1 && (
        <select
          onChange={(e) => e.target.value && scrollTo(`gen-${e.target.value}`)}
          defaultValue=""
          style={{
            backgroundColor: DARK.surface,
            border: `1px solid ${DARK.border}`,
            borderRadius: '6px',
            color: DARK.text,
            fontSize: '13px',
            padding: '5px 8px',
            cursor: 'pointer',
          }}
        >
          <option value="" disabled>Genérico…</option>
          {genericos.map((g) => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>
      )}

      {marcas.length > 1 && (
        <select
          onChange={(e) => e.target.value && scrollTo(`marca-${e.target.value}`)}
          defaultValue=""
          style={{
            backgroundColor: DARK.surface,
            border: `1px solid ${DARK.border}`,
            borderRadius: '6px',
            color: DARK.text,
            fontSize: '13px',
            padding: '5px 8px',
            cursor: 'pointer',
          }}
        >
          <option value="" disabled>Marca…</option>
          {marcas.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tabla
// ---------------------------------------------------------------------------

export default function VentasClienteTabla({ tabla }: VentasClienteTablaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  if (tabla.length === 0) {
    return (
      <div
        style={{
          padding: '40px 24px',
          textAlign: 'center',
          color: DARK.textMuted,
          fontSize: '14px',
        }}
      >
        Sin ventas en los últimos 12 meses
      </div>
    );
  }

  // Tomar los headers de la primera fila (están ordenados crono ascendente)
  const mesesKeys = getMeses(tabla[0]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <JumpToDropdowns tabla={tabla} />

      {/* Scroll container */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflow: 'auto',
          position: 'relative',
        }}
      >
        <table
          style={{
            borderCollapse: 'collapse',
            width: '100%',
            minWidth: '900px',
          }}
        >
          {/* Sticky header */}
          <thead>
            <tr>
              <th
                style={{
                  position: 'sticky',
                  top: 0,
                  left: 0,
                  zIndex: 30,
                  backgroundColor: DARK.card,
                  padding: '10px 16px',
                  textAlign: 'left',
                  fontSize: '11px',
                  color: DARK.textMuted,
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  borderBottom: `1px solid ${DARK.border}`,
                  minWidth: '220px',
                  whiteSpace: 'nowrap',
                }}
              >
                Producto
              </th>
              {mesesKeys.map((m) => (
                <th
                  key={m}
                  style={{
                    position: 'sticky',
                    top: 0,
                    zIndex: 20,
                    backgroundColor: DARK.card,
                    padding: '10px 12px',
                    textAlign: 'right',
                    fontSize: '11px',
                    color: DARK.textMuted,
                    fontWeight: '600',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    borderBottom: `1px solid ${DARK.border}`,
                    whiteSpace: 'nowrap',
                    minWidth: '60px',
                  }}
                >
                  {formatHeader(m)}
                </th>
              ))}
              <th
                style={{
                  position: 'sticky',
                  top: 0,
                  zIndex: 20,
                  backgroundColor: DARK.card,
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontSize: '11px',
                  color: DARK.textMuted,
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  borderBottom: `1px solid ${DARK.border}`,
                  whiteSpace: 'nowrap',
                  minWidth: '70px',
                }}
              >
                Total
              </th>
            </tr>
          </thead>

          <tbody>
            {tabla.map((row, i) => {
              if (isGenerico(row)) {
                return (
                  <tr
                    key={`gen-${row.generico}-${i}`}
                    id={`gen-${row.generico}`}
                    style={{ backgroundColor: '#0f1825' }}
                  >
                    <td
                      style={{
                        position: 'sticky',
                        left: 0,
                        zIndex: 10,
                        backgroundColor: '#0f1825',
                        padding: '10px 16px',
                        fontSize: '13px',
                        fontWeight: '700',
                        color: DARK.accentBlue,
                        borderBottom: `1px solid ${DARK.border}`,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {row.generico}
                    </td>
                    {mesesKeys.map((m) => (
                      <td
                        key={m}
                        style={{
                          padding: '10px 12px',
                          textAlign: 'right',
                          fontSize: '13px',
                          fontWeight: '700',
                          color: (row.meses[m] ?? 0) > 0 ? DARK.text : DARK.textMuted,
                          borderBottom: `1px solid ${DARK.border}`,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {formatVal(row.meses[m] ?? 0)}
                      </td>
                    ))}
                    <td
                      style={{
                        padding: '10px 12px',
                        textAlign: 'right',
                        fontSize: '13px',
                        fontWeight: '700',
                        color: row.total > 0 ? DARK.accentGreen : DARK.textMuted,
                        borderBottom: `1px solid ${DARK.border}`,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {formatVal(row.total)}
                    </td>
                  </tr>
                );
              }

              if (isMarca(row)) {
                return (
                  <tr
                    key={`marca-${row.generico}-${row.marca}-${i}`}
                    id={`marca-${row.marca}`}
                    style={{ backgroundColor: DARK.cardAlt }}
                  >
                    <td
                      style={{
                        position: 'sticky',
                        left: 0,
                        zIndex: 10,
                        backgroundColor: DARK.cardAlt,
                        padding: '8px 16px 8px 28px',
                        fontSize: '13px',
                        fontWeight: '600',
                        color: DARK.text,
                        borderBottom: `1px solid ${DARK.border}`,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {row.marca}
                    </td>
                    {mesesKeys.map((m) => (
                      <td
                        key={m}
                        style={{
                          padding: '8px 12px',
                          textAlign: 'right',
                          fontSize: '13px',
                          fontWeight: '600',
                          color: (row.meses[m] ?? 0) > 0 ? DARK.textSecondary : DARK.textMuted,
                          borderBottom: `1px solid ${DARK.border}`,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {formatVal(row.meses[m] ?? 0)}
                      </td>
                    ))}
                    <td
                      style={{
                        padding: '8px 12px',
                        textAlign: 'right',
                        fontSize: '13px',
                        fontWeight: '600',
                        color: row.total > 0 ? DARK.textSecondary : DARK.textMuted,
                        borderBottom: `1px solid ${DARK.border}`,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {formatVal(row.total)}
                    </td>
                  </tr>
                );
              }

              // Artículo
              const sinVentas = !hasSales(row);
              return (
                <tr
                  key={`art-${row.id_articulo}-${i}`}
                  style={{
                    backgroundColor: 'transparent',
                    opacity: sinVentas ? 0.5 : 1,
                  }}
                >
                  <td
                    style={{
                      position: 'sticky',
                      left: 0,
                      zIndex: 10,
                      backgroundColor: DARK.bg,
                      padding: '7px 16px 7px 40px',
                      fontSize: '12px',
                      fontStyle: sinVentas ? 'italic' : 'normal',
                      color: sinVentas ? DARK.textMuted : DARK.textSecondary,
                      borderBottom: `1px solid ${DARK.surface}`,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {row.articulo}
                  </td>
                  {mesesKeys.map((m) => (
                    <td
                      key={m}
                      style={{
                        padding: '7px 12px',
                        textAlign: 'right',
                        fontSize: '12px',
                        color: (row.meses[m] ?? 0) > 0 ? DARK.textSecondary : DARK.textMuted,
                        borderBottom: `1px solid ${DARK.surface}`,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {formatVal(row.meses[m] ?? 0)}
                    </td>
                  ))}
                  <td
                    style={{
                      padding: '7px 12px',
                      textAlign: 'right',
                      fontSize: '12px',
                      color: row.total > 0 ? DARK.textSecondary : DARK.textMuted,
                      borderBottom: `1px solid ${DARK.surface}`,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatVal(row.total)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
