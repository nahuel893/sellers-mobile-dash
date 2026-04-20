/**
 * VentasClientesPage — búsqueda de clientes por nombre/razón social/ID.
 *
 * Ruta: /ventas/clientes
 *
 * - Input con debounce 300ms
 * - Lista de resultados; click navega a /ventas/cliente/:id
 * - Máximo 50 resultados + aviso si hay muchos
 * - Tema oscuro
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router';
import { useVentasBuscar } from '../../hooks/ventas-mapa/use-ventas-buscar';
import type { VentasClienteBusqueda } from '../../types/ventas';
import { DARK } from '../../lib/ventas-constants';

const LIMIT = 50;
const MIN_CHARS = 2;
const DEBOUNCE_MS = 300;

// ---------------------------------------------------------------------------
// Item de resultado
// ---------------------------------------------------------------------------

interface ResultItemProps {
  cliente: VentasClienteBusqueda;
  onSelect: (c: VentasClienteBusqueda) => void;
}

function ResultItem({ cliente, onSelect }: ResultItemProps) {
  const nombre = cliente.fantasia || cliente.razon_social;
  const sub = cliente.fantasia ? cliente.razon_social : null;

  return (
    <button
      type="button"
      onClick={() => onSelect(cliente)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        padding: '12px 16px',
        width: '100%',
        textAlign: 'left',
        backgroundColor: 'transparent',
        border: 'none',
        borderBottom: `1px solid ${DARK.border}`,
        cursor: 'pointer',
        transition: 'background-color 0.1s',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.backgroundColor = DARK.surface;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent';
      }}
    >
      <span style={{ fontSize: '14px', fontWeight: '600', color: DARK.text }}>
        {nombre}
      </span>
      {sub && (
        <span style={{ fontSize: '12px', color: DARK.textSecondary }}>
          {sub}
        </span>
      )}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        {cliente.localidad && (
          <span style={{ fontSize: '11px', color: DARK.textMuted }}>
            📍 {cliente.localidad}
          </span>
        )}
        {cliente.sucursal && (
          <span style={{ fontSize: '11px', color: DARK.textMuted }}>
            🏢 {cliente.sucursal}
          </span>
        )}
        <span
          style={{
            fontSize: '11px',
            color: DARK.textMuted,
            fontFamily: 'monospace',
          }}
        >
          #{cliente.id_cliente}
        </span>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Página
// ---------------------------------------------------------------------------

export default function VentasClientesPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [inputValue, setInputValue] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');

  // Debounce
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(inputValue.trim()), DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [inputValue]);

  // Focus al montar
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const { data: resultados, isLoading } = useVentasBuscar(debouncedQ, LIMIT);

  function handleSelect(c: VentasClienteBusqueda) {
    navigate(`/ventas/cliente/${c.id_cliente}`);
  }

  const mostrandoAviso = resultados && resultados.length === LIMIT;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: DARK.bg,
        color: DARK.text,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 16px',
          backgroundColor: DARK.card,
          borderBottom: `1px solid ${DARK.border}`,
          flexShrink: 0,
        }}
      >
        <Link
          to="/ventas"
          style={{
            color: DARK.textSecondary,
            textDecoration: 'none',
            fontSize: '20px',
            lineHeight: 1,
            display: 'flex',
            alignItems: 'center',
          }}
          title="Volver al mapa"
        >
          ←
        </Link>
        <h1
          style={{
            fontSize: '15px',
            fontWeight: '700',
            color: DARK.text,
            margin: 0,
          }}
        >
          Buscar Clientes
        </h1>
      </header>

      {/* Buscador */}
      <div
        style={{
          padding: '16px',
          backgroundColor: DARK.bg,
          borderBottom: `1px solid ${DARK.border}`,
          flexShrink: 0,
        }}
      >
        <div style={{ position: 'relative', maxWidth: '600px', margin: '0 auto' }}>
          <span
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '16px',
              color: DARK.textMuted,
              pointerEvents: 'none',
            }}
          >
            🔍
          </span>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Buscá por nombre, razón social o N° de cliente…"
            style={{
              width: '100%',
              padding: '10px 12px 10px 38px',
              backgroundColor: DARK.surface,
              border: `1px solid ${DARK.border}`,
              borderRadius: '8px',
              color: DARK.text,
              fontSize: '14px',
              outline: 'none',
              boxSizing: 'border-box',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = DARK.accentBlue;
            }}
            onBlur={(e) => {
              e.target.style.borderColor = DARK.border;
            }}
          />
        </div>

        {/* Hint */}
        {debouncedQ.length > 0 && debouncedQ.length < MIN_CHARS && (
          <p
            style={{
              textAlign: 'center',
              fontSize: '12px',
              color: DARK.textMuted,
              marginTop: '8px',
            }}
          >
            Escribí al menos {MIN_CHARS} caracteres
          </p>
        )}
      </div>

      {/* Resultados */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Estado: cargando */}
        {isLoading && debouncedQ.length >= MIN_CHARS && (
          <div
            style={{
              padding: '32px',
              textAlign: 'center',
              color: DARK.textMuted,
              fontSize: '14px',
            }}
          >
            Buscando…
          </div>
        )}

        {/* Aviso: muchos resultados */}
        {mostrandoAviso && (
          <div
            style={{
              padding: '8px 16px',
              backgroundColor: DARK.surface,
              borderBottom: `1px solid ${DARK.border}`,
              fontSize: '12px',
              color: DARK.accentOrange,
              textAlign: 'center',
            }}
          >
            Mostrando {LIMIT} de muchos resultados — refiná la búsqueda
          </div>
        )}

        {/* Lista */}
        {!isLoading && resultados && resultados.length > 0 && (
          <div>
            {resultados.map((c) => (
              <ResultItem key={c.id_cliente} cliente={c} onSelect={handleSelect} />
            ))}
          </div>
        )}

        {/* Sin resultados */}
        {!isLoading &&
          debouncedQ.length >= MIN_CHARS &&
          resultados &&
          resultados.length === 0 && (
            <div
              style={{
                padding: '48px 24px',
                textAlign: 'center',
                color: DARK.textMuted,
                fontSize: '14px',
              }}
            >
              No se encontraron clientes para "{debouncedQ}"
            </div>
          )}

        {/* Estado inicial */}
        {debouncedQ.length < MIN_CHARS && !isLoading && (
          <div
            style={{
              padding: '64px 24px',
              textAlign: 'center',
              color: DARK.textMuted,
              fontSize: '14px',
            }}
          >
            Buscá un cliente para ver su historial de compras
          </div>
        )}
      </div>
    </div>
  );
}
