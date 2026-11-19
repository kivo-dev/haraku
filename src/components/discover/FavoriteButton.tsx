"use client";

import { Star } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

const KEY = "harako:favorites";

function read(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

/** Star toggle saved on this device only (until accounts exist in the backend). */
export function FavoriteButton({ id, className = "", size = "md" }: { id: string; className?: string; size?: "md" | "lg" }) {
  const t = useTranslations("Place");
  const [saved, setSaved] = useState(false);

  useEffect(() => setSaved(read().includes(id)), [id]);

  function toggle() {
    const next = !saved;
    setSaved(next);
    try {
      const list = read().filter((x) => x !== id);
      localStorage.setItem(KEY, JSON.stringify(next ? [...list, id] : list));
    } catch {
      /* storage blocked: the star still toggles for this visit */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={saved}
      aria-label={saved ? t("unsave") : t("save")}
      className={`flex items-center justify-center rounded-full bg-white/90 text-forest-900 shadow-soft transition active:scale-95 ${
        size === "lg" ? "size-14" : "size-9"
      } ${className}`}
    >
      <Star className={`${size === "lg" ? "size-6" : "size-4"} ${saved ? "fill-lime-500 text-lime-600" : ""}`} aria-hidden />
    </button>
  );
}
