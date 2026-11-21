import { categoryKeys, type CategoryKey, type LocalizedText, type Place } from "@/lib/places";
import { sectorKeys, type Opportunity, type SectorKey } from "@/lib/opportunities";

type Raw = Record<string, unknown>;
export const isObj = (v: unknown): v is Raw => typeof v === "object" && v !== null;

export function localized(v: unknown): LocalizedText | undefined {
  if (typeof v === "string" && v) return { fa: v, en: v };
  if (isObj(v)) {
    const fa = typeof v.fa === "string" ? v.fa : "";
    const en = typeof v.en === "string" ? v.en : "";
    if (fa || en) return { fa: fa || en, en: en || fa };
  }
  return undefined;
}

export function extractList(json: unknown): unknown[] | null {
  if (Array.isArray(json)) return json;
  if (isObj(json)) {
    const list = json.items ?? json.data ?? json.results;
    if (Array.isArray(list)) return list;
  }
  return null;
}

const firstImage = (raw: Raw) => {
  const image = raw.image ?? raw.imageUrl ?? raw.image_url ?? raw.photo;
  return typeof image === "string" && image ? image : undefined;
};

const categoryAliases: Record<string, CategoryKey> = {
  nature: "nature_adventure",
  history: "attractions",
  services: "public_services",
};

function normalizeCategory(value: unknown): CategoryKey | null {
  const key = String(value ?? "");
  if ((categoryKeys as readonly string[]).includes(key)) return key as CategoryKey;
  return categoryAliases[key] ?? null;
}

function normalizeImages(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const images = value
    .map((item) => {
      if (typeof item === "string") return item;
      if (isObj(item) && typeof item.url === "string") return item.url;
      return "";
    })
    .filter(Boolean);
  return images.length ? images : undefined;
}

export function normalizePlace(raw: unknown): Place | null {
  if (!isObj(raw)) return null;
  const id = raw.id ?? raw.slug;
  const name = localized(raw.name ?? raw.title);
  if ((typeof id !== "string" && typeof id !== "number") || !name) return null;

  const category = normalizeCategory(raw.category);
  if (!category) return null;

  const location = isObj(raw.location) ? raw.location : {};
  const latValue = raw.lat ?? location.lat;
  const lngValue = raw.lng ?? raw.lon ?? location.lng ?? location.lon;
  const lat = latValue === null || latValue === undefined || latValue === "" ? NaN : Number(latValue);
  const lng = lngValue === null || lngValue === undefined || lngValue === "" ? NaN : Number(lngValue);

  const ratingValue = raw.rating;
  const rating = ratingValue === null || ratingValue === undefined || ratingValue === "" ? NaN : Number(ratingValue);
  const distanceValue = raw.distanceKm ?? raw.distance_km;
  const distance = distanceValue === null || distanceValue === undefined || distanceValue === "" ? NaN : Number(distanceValue);

  return {
    id: String(id),
    category,
    name,
    area: localized(raw.area ?? raw.city ?? raw.address) ?? { fa: "", en: "" },
    summary: localized(raw.summary ?? raw.description) ?? { fa: "", en: "" },
    reason: localized(raw.reason),
    coords: Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : undefined,
    rating: Number.isFinite(rating) && rating > 0 ? rating : undefined,
    distanceKm: Number.isFinite(distance) && distance >= 0 ? distance : undefined,
    featured: raw.featured === true,
    image: firstImage(raw),
    images: normalizeImages(raw.images),
    verified: raw.verified === true,
    source: raw.is_sample === true || raw.source === "seed-sample" ? "sample" : "api",
  };
}

export function normalizeOpportunity(raw: unknown): Opportunity | null {
  if (!isObj(raw)) return null;
  const id = raw.id ?? raw.slug;
  const title = localized(raw.title ?? raw.name);
  if ((typeof id !== "string" && typeof id !== "number") || !title) return null;
  const sec = String(raw.sector ?? raw.category ?? "");
  const sector: SectorKey = (sectorKeys as readonly string[]).includes(sec) ? (sec as SectorKey) : "trade";
  return {
    id: String(id),
    sector,
    title,
    summary: localized(raw.summary ?? raw.description) ?? { fa: "", en: "" },
    image: firstImage(raw),
    source: raw.is_sample === true || raw.source === "seed-sample" ? "sample" : "api",
  };
}
