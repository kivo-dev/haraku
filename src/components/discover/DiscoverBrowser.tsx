"use client";

import { LayoutGrid, Search } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiEnabled } from "@/lib/api/config";
import { fetchPlaces } from "@/lib/api/client";
import { categoryIcons, type CategoryKey, type Category, type Place } from "@/lib/places";
import { DiscoverHero } from "./DiscoverHero";
import { PlaceCard } from "./PlaceCard";
import { Suggestions } from "./Suggestions";

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}

export function DiscoverBrowser({ places, categories }: { places: Place[]; categories: Category[] }) {
  const t = useTranslations("Discover");
  const locale = useLocale();
  const initialQuery = useSearchParams().get("q") ?? "";
  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState<CategoryKey | "all">("all");
  const debouncedQuery = useDebounced(query.trim(), 350);

  const [remote, setRemote] = useState<Place[] | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  useEffect(() => {
    if (!apiEnabled || (category === "all" && !debouncedQuery)) {
      setRemote(null);
      setStatus("idle");
      return;
    }
    const ctrl = new AbortController();
    setStatus("loading");
    fetchPlaces({ category: category === "all" ? undefined : category, q: debouncedQuery || undefined, signal: ctrl.signal })
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
  }, [category, debouncedQuery]);

  const local = useMemo(() => {
    const q = query.trim().toLowerCase();
    return places.filter(
      (p) =>
        (category === "all" || p.category === category) &&
        (!q || [p.name.fa, p.name.en, p.area.fa, p.area.en].some((s) => s.toLowerCase().includes(q))),
    );
  }, [places, query, category]);

  const visible = remote ?? local;
  const loading = status === "loading";
  const sampleData = visible.some((p) => p.source === "sample");

  return (
    <div>
      <DiscoverHero chip={t("location")} title1={t("title1")} title2={t("title2")}>
        <div
          role="search"
          className="mt-4 flex items-center gap-3 rounded-2xl bg-white px-4 shadow-soft focus-within:ring-2 focus-within:ring-lime-500 md:max-w-xl"
        >
          <Search className="size-5 shrink-0 text-forest-800" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("searchPlaceholder")}
            aria-label={t("searchLabel")}
            className="h-14 w-full bg-transparent text-base outline-none placeholder:text-ink-400"
          />
        </div>
      </DiscoverHero>

      <div className="px-5 md:px-10">
        <div className="mx-auto max-w-7xl">
          <Suggestions fallback={places} />

          <div className="no-scrollbar -mx-5 mt-6 flex gap-2 overflow-x-auto px-5 md:mx-0 md:flex-wrap md:overflow-visible md:px-0">
            {["all", ...categories.map((item) => item.key)].map((key) => {
              const item = categories.find((categoryItem) => categoryItem.key === key);
              const Icon = key === "all" ? LayoutGrid : (categoryIcons[key as CategoryKey] ?? LayoutGrid);
              const active = category === key;
              return (
                <button
                  key={key}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setCategory(key as CategoryKey | "all")}
                  className={`inline-flex h-11 shrink-0 items-center gap-2 rounded-full px-5 text-sm font-medium transition ${
                    active ? "bg-forest-950 text-white" : "bg-white text-ink-700 hover:bg-mist-50"
                  }`}
                >
                  <Icon className="size-4" aria-hidden />
                  {key === "all" ? t("all") : item?.title[locale as "fa" | "en"] ?? key}
                </button>
              );
            })}
          </div>

          <div className="mb-3 mt-6 flex items-baseline justify-between">
            <h2 className="text-lg font-semibold">{t("results")}</h2>
            <span className="text-sm text-ink-500" aria-live="polite">
              {loading ? t("loading") : t("count", { count: visible.length })}
            </span>
          </div>

          {status === "error" && (
            <p role="status" className="mb-3 rounded-2xl bg-white/80 px-4 py-3 text-sm text-ink-700">
              {t("apiError")}
            </p>
          )}

          {loading ? (
            <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 lg:grid-cols-4" aria-hidden>
              {[0, 1, 2, 3].map((i) => (
                <li key={i} className="aspect-[5/6] animate-pulse rounded-4xl bg-white/70" />
              ))}
            </ul>
          ) : visible.length > 0 ? (
            <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 lg:grid-cols-4">
              {visible.map((place) => (
                <li key={place.id}>
                  <PlaceCard place={place} />
                </li>
              ))}
            </ul>
          ) : (
            <div className="rounded-4xl bg-white p-8 text-center shadow-soft">
              <p className="font-semibold">{t("empty")}</p>
              <p className="mx-auto mt-1 max-w-xs text-sm text-ink-500">{t("emptyHint")}</p>
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  setCategory("all");
                }}
                className="mt-5 h-11 rounded-full bg-lime-400 px-6 text-sm font-semibold text-forest-950 transition hover:bg-lime-300"
              >
                {t("reset")}
              </button>
            </div>
          )}

          {sampleData && <p className="mt-6 text-center text-xs text-ink-500">{t("sampleNote")}</p>}
        </div>
      </div>
    </div>
  );
}
