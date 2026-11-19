import { MapPin } from "lucide-react";
import type { ReactNode } from "react";
import { DiscoverTabs } from "./DiscoverTabs";

/**
 * Top of both Discover pages: place chip, big fancy two-line title, the two tabs,
 * then page-specific content (search box). The paper landscape shows through below it,
 * because of the bottom padding.
 */
export function DiscoverHero({ chip, title1, title2, children }: { chip: string; title1: string; title2: string; children?: ReactNode }) {
  return (
    <div className="px-5 pb-32 pt-2 md:px-10 md:pb-48 md:pt-10">
      <div className="mx-auto max-w-7xl">
        <span className="glass inline-flex h-9 items-center gap-2 rounded-full px-3.5 text-sm font-medium text-forest-900">
          <MapPin className="size-4" aria-hidden />
          {chip}
        </span>
        <h1 className="mt-4 font-display text-[2.6rem] font-normal leading-[1.4] text-forest-950 md:text-7xl md:leading-[1.3]">
          {title1}
          <br />
          {title2}
        </h1>
        <DiscoverTabs />
        {children}
      </div>
    </div>
  );
}
