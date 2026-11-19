import { Compass } from "lucide-react";
import { Link } from "@/i18n/navigation";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link href="/" className={`flex items-center gap-2.5 text-lg font-semibold tracking-wide ${className}`}>
      <span className="flex size-9 items-center justify-center rounded-full bg-forest-900 text-lime-400">
        <Compass className="size-5" aria-hidden />
      </span>
      HARAKO
    </Link>
  );
}
