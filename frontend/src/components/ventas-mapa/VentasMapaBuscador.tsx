/**
 * VentasMapaBuscador — combobox de búsqueda de clientes sobre el mapa.
 *
 * - Debounce 300ms antes de disparar el query.
 * - Dropdown con resultados: fantasia + localidad + sucursal.
 * - Al seleccionar: flyTo al cliente (si tiene coords) y emite highlight.
 * - Si sin coords: muestra banner "Cliente sin coordenadas registradas".
 * - ESC o botón ✕ limpia todo.
 *
 * Posición: absolute top-right sobre el mapa (z-index 50).
 * ZonasBadges está en top-center → sin colisión.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import type { KeyboardEvent } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';
import { useVentasBuscar } from '../../hooks/ventas-mapa/use-ventas-buscar';
import type { VentasClienteBusqueda } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

interface VentasMapaBuscadorProps {
  /** Ref del mapa para llamar a flyTo. */
  mapRef: React.RefObject<MapRef | null>;
  /** Callback cuando el usuario selecciona un cliente (para la highlight layer). */
  onClienteSelect: (cliente: VentasClienteBusqueda | null) => void;
}

export default function VentasMapaBuscador({
  mapRef,
  onClienteSelect,
}: VentasMapaBuscadorProps) {
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [sinCoordenadas, setSinCoordenadas] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Debounce 300ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const { data: results = [] } = useVentasBuscar(debouncedQ);

  // Abrir dropdown cuando hay resultados y el input tiene foco
  useEffect(() => {
    if (results.length > 0 && q.length >= 2) {
      setOpen(true);
    } else {
      setOpen(false);
    }
    setActiveIndex(-1);
  }, [results, q]);

  const handleSelect = useCallback(
    (cliente: VentasClienteBusqueda) => {
      setQ(cliente.fantasia ?? cliente.razon_social);
      setOpen(false);
      setSinCoordenadas(false);
      onClienteSelect(cliente);

      const hasCoords =
        cliente.latitud != null && cliente.longitud != null &&
        cliente.latitud !== 0 && cliente.longitud !== 0;

      if (hasCoords && mapRef.current) {
        mapRef.current.flyTo({
          center: [cliente.longitud!, cliente.latitud!],
          zoom: 16,
          duration: 1200,
        });
      } else if (!hasCoords) {
        setSinCoordenadas(true);
      }
    },
    [mapRef, onClienteSelect],
  );

  const handleClear = useCallback(() => {
    setQ('');
    setDebouncedQ('');
    setOpen(false);
    setSinCoordenadas(false);
    setActiveIndex(-1);
    onClienteSelect(null);
    inputRef.current?.focus();
  }, [onClienteSelect]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (!open || results.length === 0) {
        if (e.key === 'Escape') handleClear();
        return;
      }
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex((prev) => Math.min(prev + 1, results.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex((prev) => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (activeIndex >= 0 && activeIndex < results.length) {
            handleSelect(results[activeIndex]);
          }
          break;
        case 'Escape':
          handleClear();
          break;
      }
    },
    [open, results, activeIndex, handleSelect, handleClear],
  );

  const listId = 'ventas-buscar-list';
  const inputId = 'ventas-buscar-input';

  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 50,
        width: '280px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}
    >
      {/* Combobox */}
      <div
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-owns={listId}
        style={{ position: 'relative' }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'rgba(15,17,23,0.92)',
            border: `1px solid ${q ? DARK.accentBlue : DARK.border}`,
            borderRadius: '6px',
            overflow: 'hidden',
          }}
        >
          <span
            style={{
              padding: '0 8px',
              color: DARK.textMuted,
              fontSize: '13px',
              userSelect: 'none',
              flexShrink: 0,
            }}
          >
            🔍
          </span>
          <input
            id={inputId}
            ref={inputRef}
            type="text"
            role="searchbox"
            aria-autocomplete="list"
            aria-controls={listId}
            aria-activedescendant={
              activeIndex >= 0 ? `ventas-buscar-option-${activeIndex}` : undefined
            }
            value={q}
            placeholder="Buscar cliente..."
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (results.length > 0 && q.length >= 2) setOpen(true);
            }}
            onBlur={() => {
              // Delay para que el click en el dropdown se procese primero
              setTimeout(() => setOpen(false), 150);
            }}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              padding: '8px 4px',
              color: DARK.text,
              fontSize: '13px',
            }}
          />
          {q && (
            <button
              type="button"
              onClick={handleClear}
              aria-label="Limpiar búsqueda"
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '0 10px',
                color: DARK.textMuted,
                fontSize: '14px',
                lineHeight: 1,
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Dropdown */}
        {open && (
          <ul
            id={listId}
            ref={listRef}
            role="listbox"
            aria-label="Resultados de búsqueda de clientes"
            style={{
              position: 'absolute',
              top: 'calc(100% + 4px)',
              left: 0,
              right: 0,
              backgroundColor: 'rgba(15,17,23,0.97)',
              border: `1px solid ${DARK.border}`,
              borderRadius: '6px',
              listStyle: 'none',
              margin: 0,
              padding: '4px 0',
              maxHeight: '260px',
              overflowY: 'auto',
              zIndex: 60,
            }}
          >
            {results.length === 0 ? (
              <li
                style={{
                  padding: '10px 12px',
                  color: DARK.textMuted,
                  fontSize: '12px',
                  textAlign: 'center',
                }}
              >
                Sin resultados
              </li>
            ) : (
              results.map((cliente, idx) => (
                <li
                  key={cliente.id_cliente}
                  id={`ventas-buscar-option-${idx}`}
                  role="option"
                  aria-selected={idx === activeIndex}
                  onMouseDown={() => handleSelect(cliente)}
                  onMouseEnter={() => setActiveIndex(idx)}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    backgroundColor:
                      idx === activeIndex ? DARK.surface : 'transparent',
                    borderRadius: '4px',
                    margin: '0 4px',
                    transition: 'background-color 0.1s',
                  }}
                >
                  <div
                    style={{
                      fontSize: '13px',
                      fontWeight: '600',
                      color: DARK.text,
                      marginBottom: '2px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cliente.fantasia ?? cliente.razon_social}
                  </div>
                  <div
                    style={{
                      fontSize: '11px',
                      color: DARK.textSecondary,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {[cliente.localidad, cliente.sucursal].filter(Boolean).join(' · ')}
                  </div>
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {/* Banner sin coordenadas */}
      {sinCoordenadas && (
        <div
          role="alert"
          style={{
            backgroundColor: 'rgba(254,243,205,0.95)',
            border: '1px solid #ffc107',
            borderRadius: '5px',
            padding: '6px 10px',
            fontSize: '11px',
            color: '#5a4a00',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>⚠</span>
          <span>Cliente sin coordenadas registradas</span>
        </div>
      )}
    </div>
  );
}
