import { Link } from 'react-router';

interface BackLinkProps {
  to: string;
  label?: string;
}

export default function BackLink({ to, label = 'Volver' }: BackLinkProps) {
  return (
    <div className="px-3 pt-4 pb-1">
      <Link
        to={to}
        className="text-sm text-ink-1 font-medium hover:text-ink-0 hover:underline no-underline"
      >
        &larr; {label}
      </Link>
    </div>
  );
}
