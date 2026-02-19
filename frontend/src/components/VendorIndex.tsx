interface VendorIndexProps {
  vendedores: Array<{ nombre: string; slug: string }>;
}

export default function VendorIndex({ vendedores }: VendorIndexProps) {
  return (
    <div className="flex flex-wrap gap-1.5 justify-center py-2 px-3">
      <a
        href="#top"
        className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-brand-dark text-white no-underline"
      >
        Inicio
      </a>
      {vendedores.map((v) => (
        <a
          key={v.slug}
          href={`#vendor-${v.slug.toLowerCase()}`}
          className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-white text-brand-dark border border-gray-300 no-underline hover:border-gray-400"
        >
          {v.nombre.split(' ')[0]}
        </a>
      ))}
    </div>
  );
}
