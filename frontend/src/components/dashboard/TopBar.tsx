
interface TopBarProps {
  /** Current seller name or "Casa Central" */
  sellerName: string;
  /** Active category key e.g. 'CERVEZAS' */
  activeCategory: string;
  /** Callback when a category pill is clicked */
  onCategoryChange: (cat: string) => void;
  /** Timestamp of last data sync */
  syncedAt?: Date;
}

const CATEGORIES = [
  { key: 'CERVEZAS',      label: 'Cervezas' },
  { key: 'MULTI_CCU',     label: 'MultiCCU' },
  { key: 'AGUAS_DANONE',  label: 'Aguas Danone' },
];

/** Formats elapsed time in Spanish */
function fmtElapsed(date: Date): string {
  const diffMin = Math.round((Date.now() - date.getTime()) / 60_000);
  if (diffMin < 1) return 'ahora mismo';
  if (diffMin === 1) return 'hace 1 min';
  if (diffMin < 60) return `hace ${diffMin} min`;
  const hours = Math.round(diffMin / 60);
  return `hace ${hours} h`;
}

export function TopBar({ sellerName, activeCategory, onCategoryChange, syncedAt }: TopBarProps) {
  return (
    <div
      className="flex items-center justify-between mb-6"
      role="banner"
    >
      {/* Brand mark + text */}
      <div className="flex items-center gap-3.5">
        {/* Brand mark: 36×36 box with inner cutout + bar decoration */}
        <div
          className="relative overflow-hidden flex-shrink-0"
          style={{
            width: 36,
            height: 36,
            borderRadius: 9,
            background: 'linear-gradient(135deg, oklch(0.86 0.18 115), oklch(0.78 0.16 145))',
          }}
          aria-hidden="true"
        >
          {/* Inner dark cutout */}
          <div
            className="absolute bg-bg-0 rounded-[6px]"
            style={{ inset: 4 }}
          />
          {/* Bar decoration */}
          <div
            className="absolute z-10 rounded-sm"
            style={{
              left: 8,
              bottom: 8,
              width: 4,
              height: 12,
              background: 'oklch(0.86 0.18 115)',
              boxShadow: '6px -3px 0 oklch(0.78 0.16 145), 12px -6px 0 var(--color-ink-0, #f5efdd)',
            }}
          />
        </div>

        <div>
          <div
            className="text-ink-2 font-sans font-semibold uppercase"
            style={{ fontSize: 10, letterSpacing: '0.18em' }}
          >
            Avance Preventistas
          </div>
          <h1
            className="text-ink-0 font-sans font-semibold mt-[2px]"
            style={{ fontSize: 17, letterSpacing: '-0.01em', margin: 0 }}
          >
            {sellerName}
          </h1>
        </div>
      </div>

      {/* Right: category tabs + sync chip */}
      <div className="flex items-center gap-3">
        {/* Category tab group */}
        <div
          className="inline-flex bg-bg-2 border border-line rounded-full p-1"
          role="tablist"
          aria-label="Categoría"
        >
          {CATEGORIES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={activeCategory === key}
              className={[
                'px-[18px] py-2 border-0 rounded-full cursor-pointer',
                'font-sans font-medium text-[13px] tracking-[-0.005em]',
                'transition-all duration-200',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime',
                activeCategory === key
                  ? 'bg-ink-0 text-bg-0 font-semibold'
                  : 'bg-transparent text-ink-2 hover:text-ink-0',
              ].join(' ')}
              onClick={() => onCategoryChange(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Sync status chip */}
        <div
          className="inline-flex items-center gap-2 px-3.5 py-2
                     bg-bg-2 border border-line rounded-full
                     text-ink-1 text-xs"
        >
          <span
            className="w-[7px] h-[7px] rounded-full bg-ok flex-shrink-0"
            style={{
              boxShadow: '0 0 0 3px color-mix(in oklch, oklch(0.78 0.16 145) 22%, transparent)',
              animation: 'pulse 2.4s infinite',
            }}
            aria-hidden="true"
          />
          <span>
            {syncedAt ? `Sync: ${fmtElapsed(syncedAt)}` : 'Sincronizando…'}
          </span>
        </div>
      </div>
    </div>
  );
}
