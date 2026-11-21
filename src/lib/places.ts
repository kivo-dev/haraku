import { BedDouble, BusFront, Landmark, MapPin, Mountain, type LucideIcon } from "lucide-react";

export const categoryKeys = [
  "attractions",
  "accommodation_food",
  "transport",
  "public_services",
  "nature_adventure",
] as const;
export type CategoryKey = (typeof categoryKeys)[number];

export const categoryIcons: Record<CategoryKey, LucideIcon> = {
  attractions: Landmark,
  accommodation_food: BedDouble,
  transport: BusFront,
  public_services: MapPin,
  nature_adventure: Mountain,
};

/** Colour mood of the placeholder illustration, per category. */
export const categoryArt: Record<CategoryKey, "forest" | "dawn" | "fog"> = {
  attractions: "dawn",
  accommodation_food: "fog",
  transport: "fog",
  public_services: "fog",
  nature_adventure: "forest",
};

export type LocalizedText = { fa: string; en: string };

export type Category = {
  key: CategoryKey;
  title: LocalizedText;
};

/** Normalized shape consumed by the UI. */
export type Place = {
  id: string;
  category: CategoryKey;
  name: LocalizedText;
  area: LocalizedText;
  summary: LocalizedText;
  coords?: { lat: number; lng: number };
  rating?: number;
  distanceKm?: number;
  image?: string;
  images?: string[];
  reason?: LocalizedText;
  featured?: boolean;
  verified?: boolean;
  source: "sample" | "api";
};

export const defaultCategories: Category[] = [
  { key: "attractions", title: { fa: "جاذبه‌های گردشگری", en: "Tourist attractions" } },
  { key: "accommodation_food", title: { fa: "اقامت و پذیرایی", en: "Accommodation and dining" } },
  { key: "transport", title: { fa: "حمل‌ونقل", en: "Transportation" } },
  { key: "public_services", title: { fa: "خدمات عمومی", en: "Public services" } },
  { key: "nature_adventure", title: { fa: "طبیعت و ماجراجویی", en: "Nature and adventure" } },
];

// SAMPLE DATA ONLY: unverified placeholders, never presented as verified records.
export const samplePlaces: Place[] = [
  {
    id: "maku-viewpoint",
    featured: true,
    category: "nature_adventure",
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
    category: "attractions",
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
    category: "nature_adventure",
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
    category: "transport",
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
