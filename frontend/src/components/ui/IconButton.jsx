import React, { forwardRef } from 'react';
import { cn } from '../../lib/cn';

const VARIANTS = {
  default: 'text-muted hover:text-foreground hover:bg-surface',
  brand: 'text-brand hover:bg-brand/10',
  danger: 'text-muted hover:text-rose-300 hover:bg-rose-500/10',
  subtle: 'text-muted border border-border hover:text-foreground hover:bg-surface',
};

const IconButton = forwardRef(function IconButton(
  { className, variant = 'default', size = 'md', label, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex items-center justify-center rounded-lg transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50',
        size === 'sm' ? 'h-7 w-7' : 'h-9 w-9',
        VARIANTS[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});

export default IconButton;
