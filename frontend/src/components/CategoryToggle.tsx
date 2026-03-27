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
              ? 'bg-brand-dark text-white border-brand-dark'
              : 'bg-white text-brand-dark border-gray-300 hover:border-gray-400'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
