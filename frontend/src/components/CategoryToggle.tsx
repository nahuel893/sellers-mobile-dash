interface CategoryToggleProps {
  activeIndex: number;
  onChange: (index: number) => void;
}

const SLIDE_LABELS = ['Cervezas', 'MultiCCU / Aguas Danone'];

export default function CategoryToggle({ activeIndex, onChange }: CategoryToggleProps) {
  return (
    <div className="flex gap-1.5 justify-center py-2 px-3 flex-wrap">
      {SLIDE_LABELS.map((label, i) => (
        <button
          key={label}
          onClick={() => onChange(i)}
          className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors ${
            i === activeIndex
              ? 'bg-ink-0 text-bg-0 border-ink-0'
              : 'bg-bg-2 text-ink-1 border-line hover:border-ink-2'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
