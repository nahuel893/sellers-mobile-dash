interface VendorIndexProps {
  vendedores: Array<{ nombre: string; slug: string }>;
}

export default function VendorIndex({ vendedores }: VendorIndexProps) {
  return (
    <div className="flex flex-wrap gap-1.5 justify-center py-2 px-3">
      <a
        href="#top"
        className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-ink-0 text-bg-0 no-underline"
      >
        Inicio
      </a>
      {vendedores.map((v) => (
        <a
          key={v.slug}
          href={`#vendor-${v.slug.toLowerCase()}`}
          className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-bg-2 text-ink-1 border border-line no-underline hover:border-ink-2"
        >
          {v.nombre.split(' ')[0]}
        </a>
      ))}
    </div>
  );
}
