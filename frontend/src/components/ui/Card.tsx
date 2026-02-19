import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      className={`bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-4 transition-colors ${onClick ? 'cursor-pointer hover:border-primary-500' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
