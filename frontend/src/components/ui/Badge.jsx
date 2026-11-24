import React from 'react';
import { cn } from '../../lib/cn';

const VARIANTS = {
  default: 'bg-surface text-muted border-border',
  brand: 'bg-brand/10 text-brand border-brand/30',
  success: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  danger: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
  neutral: 'bg-transparent text-muted-dim border-border-subtle',
};

export default function Badge({ children, variant = 'default', className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide',
        VARIANTS[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
