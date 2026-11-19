import { categoryKeys, type CategoryKey, type LocalizedText, type Place } from "@/lib/places";
import { sectorKeys, type Opportunity, type SectorKey } from "@/lib/opportunities";

/**
 * The ONLY place that knows the API's field names.
 * When the real backend / Neshan response is final, adjust these functions and nothing else changes.
 * Expected fields are documented in README.md ("API contract").
 */
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

/** A list can arrive as `[...]` or as `{ items | data | results: [...] }`. */
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

export function normalizePlace(raw: unknown): Place | null {
  if (!isObj(raw)) return null;
  const id = raw.id ?? raw.slug;
  const name = localized(raw.name ?? raw.title);
  if ((typeof id !== "string" && typeof id !== "number") || !name) return null;

  const cat = String(raw.category ?? "");
  const category: CategoryKey = (categoryKeys as readonly string[]).includes(cat) ? (cat as CategoryKey) : "nature";
  const lat = Number(raw.lat ?? (isObj(raw.location) ? raw.location.lat : undefined));
  const lng = Number(raw.lng ?? raw.lon ?? (isObj(raw.location) ? (raw.location.lng ?? raw.location.lon) : undefined));
  const rating = Number(raw.rating);
  const distance = Number(raw.distanceKm ?? raw.distance_km);

  return {
    id: String(id),
    category,
    name,
    area: localized(raw.area ?? raw.city ?? raw.address) ?? { fa: "", en: "" },
    summary: localized(raw.summary ?? raw.description) ?? { fa: "", en: "" },
    reason: localized(raw.reason),
    coords: Number.isFinite(lat) && Number.isFinite(lng) && raw.lat !== undefined ? { lat, lng } : undefined,
    rating: Number.isFinite(rating) && rating > 0 ? rating : undefined,
    distanceKm: Number.isFinite(distance) && distance >= 0 && raw.distanceKm !== undefined ? distance : undefined,
    featured: raw.featured === true,
    image: firstImage(raw),
    source: "api",
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
    source: "api",
  };
}
