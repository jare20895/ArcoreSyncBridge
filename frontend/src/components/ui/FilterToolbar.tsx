import React from 'react';

type FilterToolbarProps = {
  children: React.ReactNode;
  className?: string;
};

export function FilterToolbar({ children, className = '' }: FilterToolbarProps) {
  return <div className={`mb-4 grid gap-3 ${className}`.trim()}>{children}</div>;
}
