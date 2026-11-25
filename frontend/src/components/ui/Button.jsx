import React, { forwardRef } from 'react';
import { cn } from '../../lib/cn';

const VARIANTS = {
  primary:
    'bg-brand text-brand-foreground hover:bg-brand-hover shadow-carbon-sm disabled:hover:bg-brand',
  secondary:
    'bg-surface text-foreground border border-border hover:bg-[#2F2F2F] hover:border-[#3A4046]',
  ghost:
    'bg-transparent text-muted hover:bg-surface hover:text-foreground',
  subtle:
    'bg-surface-raised text-foreground border border-border-subtle hover:border-border hover:bg-surface',
  danger:
    'bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20',
};

const SIZES = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-sm gap-2',
  icon: 'h-9 w-9 p-0 justify-center',
  'icon-sm': 'h-7 w-7 p-0 justify-center',
};

const Button = forwardRef(function Button(
  { className, variant = 'primary', size = 'md', type = 'button', disabled, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-semibold transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        'disabled:cursor-not-allowed disabled:opacity-40',
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});

export default Button;
