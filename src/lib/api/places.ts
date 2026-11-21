import { sampleOpportunities, type Opportunity } from "@/lib/opportunities";
import { categoryKeys, defaultCategories, samplePlaces, type Category, type CategoryKey, type Place } from "@/lib/places";
import { API_BASE } from "./config";
import { extractList, isObj, localized, normalizeOpportunity, normalizePlace } from "./normalize";

const REVALIDATE_SECONDS = 300;

async function request(path: string): Promise<unknown | null> {
  if (!API_BASE) return null;
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: REVALIDATE_SECONDS },
      signal: AbortSignal.timeout(5000),
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/** With API configured, an empty/error response stays empty; prototype data is never substituted. */
export async function getPlaces(): Promise<Place[]> {
  if (!API_BASE) return samplePlaces;
  const list = extractList(await request("/places"));
  return (list ?? []).map(normalizePlace).filter((p): p is Place => p !== null);
}

export async function getPlace(id: string): Promise<Place | null> {
  if (!API_BASE) return samplePlaces.find((p) => p.id === id) ?? null;
  const json = await request(`/places/${encodeURIComponent(id)}`);
  return normalizePlace(isObj(json) && isObj(json.data) ? json.data : json);
}

export async function getOpportunities(): Promise<Opportunity[]> {
  if (!API_BASE) return sampleOpportunities;
  const list = extractList(await request("/opportunities"));
  return (list ?? []).map(normalizeOpportunity).filter((o): o is Opportunity => o !== null);
}

export async function getCategories(): Promise<Category[]> {
  if (!API_BASE) return defaultCategories;
  const list = extractList(await request("/categories"));
  const categories = (list ?? [])
    .filter(isObj)
    .map((row) => {
      const title = localized(row.title);
      const rawKey = String(row.key ?? "");
      const key = (categoryKeys as readonly string[]).includes(rawKey) ? (rawKey as CategoryKey) : null;
      return title && key ? { key, title } : null;
    })
    .filter((item): item is Category => item !== null);
  return categories.length ? categories : defaultCategories;
}
