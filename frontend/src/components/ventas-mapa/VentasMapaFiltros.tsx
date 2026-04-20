/**
 * Drawer de filtros del mapa de ventas.
 * Se abre desde la derecha. Sin cascada reactiva (Fase 3 simplification).
 * Todos los valores vienen de /api/ventas-filtros/opciones en una sola llamada.
 */
import type { VentasFiltrosOpciones, VentasFiltrosState, VentasFV, VentasTipoSucursal, VentasZonasAgrupacion } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasMapaFiltrosProps {
  open: boolean;
  onClose: () => void;
  opciones: VentasFiltrosOpciones | undefined;
  filtros: VentasFiltrosState;
  onChange: (filtros: VentasFiltrosState) => void;
  onAplicar: () => void;
  onLimpiar: () => void;
}

// ---------------------------------------------------------------------------
// Sub-componentes de UI
// ---------------------------------------------------------------------------

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label style={{ display: 'block', fontSize: '11px', color: DARK.textSecondary, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      {children}
    </label>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: '10px', fontWeight: '700', color: DARK.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '16px', marginBottom: '8px', borderBottom: `1px solid ${DARK.border}`, paddingBottom: '4px' }}>
      {children}
    </div>
  );
}

function DateInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ flex: 1 }}>
      <Label>{label}</Label>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: '100%',
          backgroundColor: DARK.surface,
          border: `1px solid ${DARK.border}`,
          borderRadius: '4px',
          color: DARK.text,
          padding: '6px 8px',
          fontSize: '12px',
        }}
      />
    </div>
  );
}

function MultiSelectListbox({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  const toggle = (val: string) => {
    if (selected.includes(val)) {
      onChange(selected.filter((v) => v !== val));
    } else {
      onChange([...selected, val]);
    }
  };

  return (
    <div>
      <Label>
        {label}
        {selected.length > 0 && (
          <span style={{ marginLeft: '6px', color: DARK.accentBlue, fontWeight: 'bold' }}>
            ({selected.length})
          </span>
        )}
      </Label>
      <div
        style={{
          maxHeight: '110px',
          overflowY: 'auto',
          backgroundColor: DARK.surface,
          border: `1px solid ${DARK.border}`,
          borderRadius: '4px',
        }}
      >
        {options.length === 0 && (
          <div style={{ padding: '8px', color: DARK.textMuted, fontSize: '11px' }}>Sin opciones</div>
        )}
        {options.map((op) => (
          <label
            key={op}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 8px',
              cursor: 'pointer',
              fontSize: '12px',
              color: selected.includes(op) ? DARK.text : DARK.textSecondary,
              backgroundColor: selected.includes(op) ? DARK.cardAlt : 'transparent',
            }}
          >
            <input
              type="checkbox"
              checked={selected.includes(op)}
              onChange={() => toggle(op)}
              style={{ accentColor: DARK.accentBlue }}
            />
            {op}
          </label>
        ))}
      </div>
    </div>
  );
}

function RadioGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {options.map((op) => (
          <label
            key={op.value}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              color: value === op.value ? DARK.text : DARK.textSecondary,
            }}
          >
            <input
              type="radio"
              name={label}
              value={op.value}
              checked={value === op.value}
              onChange={() => onChange(op.value)}
              style={{ accentColor: DARK.accentBlue }}
            />
            {op.label}
          </label>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Drawer principal
// ---------------------------------------------------------------------------

export default function VentasMapaFiltros({
  open,
  onClose,
  opciones,
  filtros,
  onChange,
  onAplicar,
  onLimpiar,
}: VentasMapaFiltrosProps) {
  const set = <K extends keyof VentasFiltrosState>(key: K, value: VentasFiltrosState[K]) => {
    onChange({ ...filtros, [key]: value });
  };

  const sucursalOptions = opciones?.sucursales.map((s) => s.des_sucursal) ?? [];
  const selectedSucursales = filtros.sucursal_ids
    .map((id) => opciones?.sucursales.find((s) => s.id_sucursal === id)?.des_sucursal)
    .filter(Boolean) as string[];

  const handleSucursalesChange = (names: string[]) => {
    const ids = names
      .map((name) => opciones?.sucursales.find((s) => s.des_sucursal === name)?.id_sucursal)
      .filter((id): id is number => id !== undefined);
    set('sucursal_ids', ids);
  };

  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 200,
          }}
        />
      )}

      {/* Drawer */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '320px',
          backgroundColor: DARK.card,
          borderLeft: `1px solid ${DARK.border}`,
          zIndex: 201,
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s ease-in-out',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 16px',
            borderBottom: `1px solid ${DARK.border}`,
          }}
        >
          <span style={{ color: DARK.text, fontWeight: '700', fontSize: '14px' }}>Filtros</span>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: DARK.textSecondary, cursor: 'pointer', fontSize: '18px', lineHeight: 1 }}
            aria-label="Cerrar filtros"
          >
            ✕
          </button>
        </div>

        {/* Contenido scrolleable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>

          <SectionTitle>Período</SectionTitle>
          <div style={{ display: 'flex', gap: '8px' }}>
            <DateInput label="Desde" value={filtros.fecha_ini} onChange={(v) => set('fecha_ini', v)} />
            <DateInput label="Hasta" value={filtros.fecha_fin} onChange={(v) => set('fecha_fin', v)} />
          </div>

          <SectionTitle>Segmentación</SectionTitle>
          <MultiSelectListbox
            label="Canal"
            options={opciones?.canales ?? []}
            selected={filtros.canal}
            onChange={(v) => set('canal', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Subcanal"
            options={opciones?.subcanales ?? []}
            selected={filtros.subcanal}
            onChange={(v) => set('subcanal', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Localidad"
            options={opciones?.localidades ?? []}
            selected={filtros.localidad}
            onChange={(v) => set('localidad', v)}
          />

          <SectionTitle>Comercial</SectionTitle>
          <RadioGroup<VentasFV>
            label="Fuerza de Venta"
            options={[
              { value: '1', label: 'FV1' },
              { value: '4', label: 'FV4' },
              { value: 'AMBAS', label: 'Ambas' },
            ]}
            value={filtros.fv}
            onChange={(v) => set('fv', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Preventista"
            options={opciones?.preventistas ?? []}
            selected={filtros.preventistas}
            onChange={(v) => set('preventistas', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Ruta"
            options={opciones?.rutas ?? []}
            selected={filtros.rutas}
            onChange={(v) => set('rutas', v)}
          />

          <SectionTitle>Sucursal</SectionTitle>
          <RadioGroup<VentasTipoSucursal>
            label="Tipo"
            options={[
              { value: 'TODAS', label: 'Todas' },
              { value: 'SUCURSALES', label: 'Sucursales' },
              { value: 'CASA_CENTRAL', label: 'Casa Central' },
            ]}
            value={filtros.tipo_sucursal}
            onChange={(v) => set('tipo_sucursal', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Sucursal"
            options={sucursalOptions}
            selected={selectedSucursales}
            onChange={handleSucursalesChange}
          />

          <SectionTitle>Lista de Precio</SectionTitle>
          <div
            style={{
              maxHeight: '90px',
              overflowY: 'auto',
              backgroundColor: DARK.surface,
              border: `1px solid ${DARK.border}`,
              borderRadius: '4px',
            }}
          >
            {(opciones?.listas_precio ?? []).map((lp) => (
              <label
                key={lp.id_lista_precio}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '4px 8px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  color: filtros.lista_precio.includes(lp.id_lista_precio) ? DARK.text : DARK.textSecondary,
                  backgroundColor: filtros.lista_precio.includes(lp.id_lista_precio) ? DARK.cardAlt : 'transparent',
                }}
              >
                <input
                  type="checkbox"
                  checked={filtros.lista_precio.includes(lp.id_lista_precio)}
                  onChange={() => {
                    const cur = filtros.lista_precio;
                    set(
                      'lista_precio',
                      cur.includes(lp.id_lista_precio)
                        ? cur.filter((id) => id !== lp.id_lista_precio)
                        : [...cur, lp.id_lista_precio],
                    );
                  }}
                  style={{ accentColor: DARK.accentBlue }}
                />
                {lp.des_lista_precio ?? `LP ${lp.id_lista_precio}`}
              </label>
            ))}
          </div>

          <SectionTitle>Producto</SectionTitle>
          <MultiSelectListbox
            label="Genérico"
            options={opciones?.genericos ?? []}
            selected={filtros.genericos}
            onChange={(v) => set('genericos', v)}
          />
          <div style={{ marginTop: '8px' }} />
          <MultiSelectListbox
            label="Marca"
            options={opciones?.marcas ?? []}
            selected={filtros.marcas}
            onChange={(v) => set('marcas', v)}
          />

          <SectionTitle>Zonas</SectionTitle>
          <RadioGroup<VentasZonasAgrupacion>
            label="Mostrar zonas"
            options={[
              { value: 'OCULTAS', label: 'Ocultas' },
              { value: 'ruta', label: 'Por Ruta' },
              { value: 'preventista', label: 'Por Preventista' },
            ]}
            value={filtros.zonas_agrupacion}
            onChange={(v) => set('zonas_agrupacion', v)}
          />

        </div>

        {/* Footer con acciones */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            padding: '12px 16px',
            borderTop: `1px solid ${DARK.border}`,
          }}
        >
          <button
            type="button"
            onClick={onLimpiar}
            style={{
              flex: 1,
              padding: '8px',
              fontSize: '13px',
              backgroundColor: 'transparent',
              border: `1px solid ${DARK.border}`,
              borderRadius: '6px',
              color: DARK.textSecondary,
              cursor: 'pointer',
            }}
          >
            Limpiar
          </button>
          <button
            type="button"
            onClick={() => { onAplicar(); onClose(); }}
            style={{
              flex: 2,
              padding: '8px',
              fontSize: '13px',
              fontWeight: '700',
              backgroundColor: DARK.accentBlue,
              border: 'none',
              borderRadius: '6px',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            Aplicar
          </button>
        </div>
      </div>
    </>
  );
}
