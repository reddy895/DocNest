import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/cn';

export default function Spinner({ className, size = 16, label = 'Loading' }) {
  return (
    <span role="status" aria-label={label} className="inline-flex items-center justify-center">
      <Loader2 className={cn('animate-spin text-brand', className)} style={{ width: size, height: size }} />
      <span className="sr-only">{label}</span>
    </span>
  );
}
