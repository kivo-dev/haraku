"use client";

import { RefreshCw } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiEnabled } from "@/lib/api/config";
import { fetchSuggestions } from "@/lib/api/client";
import type { Place } from "@/lib/places";
import { PlaceCard } from "./PlaceCard";

const AUTOPLAY_MS = 6000;

function shuffled<T>(list: T[]): T[] {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/**
 * "Our suggestions": a carousel that is filled by the backend (`GET /suggestions`) every time the
 * screen opens and when the user taps refresh. Until a backend exists it shuffles the sample places,
 * so the behaviour can be tested. It slides on its own every few seconds (not with "reduce motion").
 */
export function Suggestions({ fallback }: { fallback: Place[] }) {
  const t = useTranslations("Discover");
  // Same order on the server and on the first client render; the real list arrives after mount.
  const [items, setItems] = useState<Place[]>(fallback.slice(0, 6));
  const [loading, setLoading] = useState(false);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const cards = useRef<(HTMLLIElement | null)[]>([]);
  const moved = useRef(false);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      try {
        const list = apiEnabled ? await fetchSuggestions({ signal }) : [];
        setItems(list.length > 0 ? list : shuffled(fallback).slice(0, 6));
      } catch (e) {
        if ((e as Error).name !== "AbortError") setItems(shuffled(fallback).slice(0, 6));
      } finally {
        setLoading(false);
        setIndex(0);
      }
    },
    [fallback],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  // Slide on its own
  useEffect(() => {
    if (items.length < 2 || paused) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % items.length), AUTOPLAY_MS);
    return () => clearInterval(id);
  }, [items.length, paused]);

  useEffect(() => {
    if (!moved.current) {
      moved.current = true;
      return;
    }
    cards.current[index]?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "start" });
  }, [index]);

  return (
    <section
      aria-labelledby="suggestions-title"
      className="rounded-5xl bg-white/75 p-4 shadow-soft backdrop-blur-sm md:p-6"
      onPointerEnter={() => setPaused(true)}
      onPointerLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 id="suggestions-title" className="font-display text-2xl font-normal leading-9 text-forest-950 md:text-3xl">
            {t("suggestionsTitle")}
          </h2>
          <p className="mt-0.5 text-sm text-ink-500">{t("suggestionsHint")}</p>
        </div>
        <button
          type="button"
          onClick={() => load()}
          disabled={loading}
          aria-label={t("refresh")}
          className="flex size-11 shrink-0 items-center justify-center rounded-full bg-lime-400 text-forest-950 transition hover:bg-lime-300 disabled:opacity-70"
        >
          <RefreshCw className={`size-5 ${loading ? "animate-spin" : ""}`} aria-hidden />
        </button>
      </div>

      <ul className="no-scrollbar -mx-4 mt-4 flex snap-x snap-mandatory scroll-px-4 gap-3 overflow-x-auto px-4 pb-1 md:mx-0 md:px-0">
        {items.map((place, i) => (
          <li
            key={place.id}
            ref={(el) => {
              cards.current[i] = el;
            }}
            className="w-[84%] shrink-0 snap-start md:w-[26rem]"
          >
            <PlaceCard place={place} variant="wide" priority={i === 0} />
          </li>
        ))}
      </ul>

      {items.length > 1 && (
        <div className="mt-3 flex justify-center gap-1.5" aria-hidden>
          {items.map((p, i) => (
            <span key={p.id} className={`h-1.5 rounded-full transition-all ${i === index ? "w-5 bg-forest-900" : "w-1.5 bg-forest-900/25"}`} />
          ))}
        </div>
      )}
    </section>
  );
}
