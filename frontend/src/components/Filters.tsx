interface FiltersProps {
  sucursales: string[];
  selectedSucursal: string | null;
  onSucursalChange: (value: string) => void;
  supervisores: string[];
  selectedSupervisor: string | null;
  onSupervisorChange: (value: string) => void;
  isLoadingSupervisores?: boolean;
}

export default function Filters({
  sucursales,
  selectedSucursal,
  onSucursalChange,
  supervisores,
  selectedSupervisor,
  onSupervisorChange,
  isLoadingSupervisores,
}: FiltersProps) {
  return (
    <div className="flex gap-2.5 px-3 py-3 xl:flex-col">
      <FilterSelect
        label="Sucursal"
        options={sucursales}
        value={selectedSucursal}
        onChange={onSucursalChange}
      />
      <FilterSelect
        label="Supervisor"
        options={supervisores}
        value={selectedSupervisor}
        onChange={onSupervisorChange}
        disabled={isLoadingSupervisores}
        placeholder={isLoadingSupervisores ? 'Cargando...' : 'Seleccionar'}
      />
    </div>
  );
}

function FilterSelect({
  label,
  options,
  value,
  onChange,
  disabled,
  placeholder = 'Seleccionar',
}: {
  label: string;
  options: string[];
  value: string | null;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  return (
    <div className="flex-1">
      <label className="block text-[10px] uppercase tracking-wider text-ink-2 font-semibold mb-1">
        {label}
      </label>
      <select
        className="w-full rounded-[10px] border border-line bg-bg-2 px-3 py-2 text-sm text-ink-0 font-medium appearance-none cursor-pointer focus:outline-none focus:border-ink-2"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {!value && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
