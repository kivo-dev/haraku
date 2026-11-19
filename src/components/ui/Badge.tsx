import type { ReactNode } from "react";

export function Badge({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-forest-800 ${className}`}
    >
      <span className="size-1.5 rounded-full bg-lime-500" aria-hidden />
      {children}
    </span>
  );
}
