"use client";

import { Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState, type FormEvent } from "react";
import { useRouter } from "@/i18n/navigation";

/** Pill search on the landing page; sends the visitor to Discover with ?q= filled in. */
export function LandingSearch() {
  const t = useTranslations("Landing");
  const router = useRouter();
  const [q, setQ] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const query = q.trim();
    router.push(query ? { pathname: "/discover", query: { q: query } } : "/discover");
  }

  return (
    <form
      role="search"
      onSubmit={submit}
      className="glass flex w-full max-w-lg items-center gap-2 rounded-full p-1.5 ps-5 shadow-float"
    >
      <Search className="size-5 shrink-0 text-forest-700" aria-hidden />
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("searchPlaceholder")}
        aria-label={t("searchLabel")}
        className="h-11 min-w-0 flex-1 bg-transparent text-base text-ink-900 outline-none placeholder:text-ink-500"
      />
      <button
        type="submit"
        className="h-11 shrink-0 rounded-full bg-forest-950 px-6 text-sm font-medium text-white transition hover:bg-forest-800"
      >
        {t("searchButton")}
      </button>
    </form>
  );
}
