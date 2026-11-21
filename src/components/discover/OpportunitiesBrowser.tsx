"use client";

import { LayoutGrid } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
import { apiEnabled } from "@/lib/api/config";
import { fetchOpportunities } from "@/lib/api/client";
import { sectorIcons, sectorKeys, type Opportunity, type SectorKey } from "@/lib/opportunities";
import { DiscoverHero } from "./DiscoverHero";
import { OpportunityCard } from "./OpportunityCard";

const filters = ["all", ...sectorKeys] as const;

/**
 * Discover, page 2: economic opportunities of the city.
 * Picking a sector asks the backend (`GET /opportunities?sector=`); without a backend the
 * built-in placeholders are filtered on the device.
 */
export function OpportunitiesBrowser({ items, loadFailed = false }: { items: Opportunity[]; loadFailed?: boolean }) {
  const t = useTranslations("Opportunities");
  const td = useTranslations("Discover");
  const [sector, setSector] = useState<SectorKey | "all">("all");
  const [remote, setRemote] = useState<Opportunity[] | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  useEffect(() => {
    if (!apiEnabled || sector === "all") {
      setRemote(null);
      setStatus("idle");
      return;
    }
    const ctrl = new AbortController();
    setStatus("loading");
    fetchOpportunities({ sector, signal: ctrl.signal })
      .then((list) => {
        setRemote(list);
        setStatus("idle");
      })
      .catch((e: Error) => {
        if (e.name === "AbortError") return;
        setRemote(null);
        setStatus("error");
      });
    return () => ctrl.abort();
  }, [sector]);

  const local = useMemo(() => items.filter((o) => sector === "all" || o.sector === sector), [items, sector]);
  const visible = remote ?? local;
  const loading = status === "loading";

  return (
    <div>
      <DiscoverHero chip={td("location")} title1={t("title1")} title2={t("title2")} />

      <div className="px-5 md:px-10">
        <div className="mx-auto max-w-7xl">
          <p className="mb-4 max-w-md text-ink-700">{t("hint")}</p>
          <div className="no-scrollbar -mx-5 flex gap-2 overflow-x-auto px-5 md:mx-0 md:flex-wrap md:overflow-visible md:px-0">
            {filters.map((key) => {
              const Icon = key === "all" ? LayoutGrid : sectorIcons[key];
              const active = sector === key;
              return (
                <button
                  key={key}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setSector(key)}
                  className={`inline-flex h-11 shrink-0 items-center gap-2 rounded-full px-5 text-sm font-medium transition ${
                    active ? "bg-forest-950 text-white" : "bg-white text-ink-700 hover:bg-mist-50"
                  }`}
                >
                  <Icon className="size-4" aria-hidden />
                  {key === "all" ? td("all") : t(`sectors.${key}`)}
                </button>
              );
            })}
          </div>

          <div className="mb-3 mt-6 flex items-baseline justify-between">
            <h2 className="text-lg font-semibold">{t("results")}</h2>
            <span className="text-sm text-ink-500" aria-live="polite">
              {loading ? td("loading") : t("count", { count: visible.length })}
            </span>
          </div>

          {loadFailed && (
            <p role="alert" className="mb-3 rounded-2xl bg-white/80 px-4 py-3 text-sm text-ink-700">
              {td("serverDown")}
            </p>
          )}
          {status === "error" && (
            <p role="status" className="mb-3 rounded-2xl bg-white/80 px-4 py-3 text-sm text-ink-700">
              {td("apiError")}
            </p>
          )}

          {loading ? (
            <ul className="grid gap-3 md:grid-cols-2 md:gap-5" aria-hidden>
              {[0, 1].map((i) => (
                <li key={i} className="h-36 animate-pulse rounded-4xl bg-white/70" />
              ))}
            </ul>
          ) : visible.length > 0 ? (
            <ul className="grid gap-3 md:grid-cols-2 md:gap-5">
              {visible.map((item) => (
                <li key={item.id}>
                  <OpportunityCard item={item} />
                </li>
              ))}
            </ul>
          ) : (
            <div className="rounded-4xl bg-white p-8 text-center shadow-soft">
              <p className="font-semibold">{t("empty")}</p>
              <p className="mx-auto mt-1 max-w-xs text-sm text-ink-500">{t("emptyHint")}</p>
            </div>
          )}

          {visible.some((o) => o.source === "sample") && <p className="mt-6 text-center text-xs text-ink-500">{t("sampleNote")}</p>}
        </div>
      </div>
    </div>
  );
}
