import { Landmark, MapPin, Mountain, type LucideIcon } from "lucide-react";

export const categoryKeys = ["nature", "history", "services"] as const;
export type CategoryKey = (typeof categoryKeys)[number];

export const categoryIcons: Record<CategoryKey, LucideIcon> = {
  nature: Mountain,
  history: Landmark,
  services: MapPin,
};

/** Colour mood of the placeholder illustration, per category. */
export const categoryArt: Record<CategoryKey, "forest" | "dawn" | "fog"> = {
  nature: "forest",
  history: "dawn",
  services: "fog",
};

export type LocalizedText = { fa: string; en: string };

/**
 * The shape the UI works with. Whatever the backend / Neshan API returns is
 * converted into this in `lib/api/places.ts` (see `normalizePlace`).
 */
export type Place = {
  id: string;
  category: CategoryKey;
  name: LocalizedText;
  area: LocalizedText;
  summary: LocalizedText;
  coords?: { lat: number; lng: number };
  /** 0–5. Shown only when present. */
  rating?: number;
  /** Distance from the user in km. Shown only when present. */
  distanceKm?: number;
  /** Full image URL from the API. When missing, /images/places/<id>.jpg is used. */
  image?: string;
  /** Why this place is suggested (used by the "Our suggestions" section). Optional. */
  reason?: LocalizedText;
  /** Shown in the wide carousel at the top of Discover. */
  featured?: boolean;
  /** "sample" = built-in prototype data, "api" = came from the backend. */
  source: "sample" | "api";
};

// SAMPLE DATA ONLY: used until the API is connected (or when it is unreachable).
// Names come from the design draft and are unverified. No coordinates on purpose.
export const samplePlaces: Place[] = [
  {
    id: "maku-viewpoint",
    featured: true,
    category: "nature",
    name: { fa: "چشم‌انداز ماکو", en: "Maku Viewpoint" },
    area: { fa: "ماکو", en: "Maku" },
    summary: {
      fa: "نقطه‌ای برای دیدن شهر و صخره‌های اطرافش از بالا.",
      en: "A spot to see the town and the rock walls around it from above.",
    },
    source: "sample",
  },
  {
    id: "qareh-kelisa",
    featured: true,
    category: "history",
    name: { fa: "قره‌کلیسا", en: "Qareh Kelisa" },
    area: { fa: "حوالی چالدران", en: "Near Chaldoran" },
    summary: {
      fa: "یکی از شناخته‌شده‌ترین بناهای تاریخی شمال غرب ایران.",
      en: "One of the best-known historic landmarks in north-west Iran.",
    },
    source: "sample",
  },
  {
    id: "chashmeh-soraya",
    category: "nature",
    name: { fa: "چشمه ثریا", en: "Chashmeh Soraya" },
    area: { fa: "ماکو", en: "Maku" },
    summary: {
      fa: "یکی از مکان‌های طبیعی پیشنهادی ماکو. متن این مکان را خودتان ویرایش کنید.",
      en: "A suggested natural place in Maku. Edit this text yourself.",
    },
    source: "sample",
  },
  {
    id: "bazargan-stop",
    category: "services",
    name: { fa: "توقف در بازرگان", en: "Stop at Bazargan" },
    area: { fa: "بازرگان", en: "Bazargan" },
    summary: {
      fa: "ایستگاهی برای استراحت، خرید و خدمات مسیر.",
      en: "A stop for a rest, shopping and services along the route.",
    },
    source: "sample",
  },
];

export function pick(text: LocalizedText, locale: string): string {
  return locale === "fa" ? text.fa : text.en;
}
