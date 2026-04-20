import { Link } from 'react-router';
import type { ReactNode } from 'react';

export interface DashboardCardDef {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: ReactNode;
  allowedRoles?: string[];
}

interface DashboardCardProps {
  card: DashboardCardDef;
}

export default function DashboardCard({ card }: DashboardCardProps) {
  return (
    <Link
      to={card.href}
      className="block bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md active:scale-[0.98] transition-all no-underline"
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-brand-dark to-brand-dark2 flex items-center justify-center text-white text-2xl">
          {card.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-extrabold text-brand-dark leading-tight">{card.title}</h2>
          <p className="text-sm text-gray-500 mt-1 leading-snug">{card.description}</p>
        </div>
        <div className="flex-shrink-0 text-gray-300 self-center">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M7.5 15l5-5-5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
