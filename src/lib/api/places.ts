import { sampleOpportunities, type Opportunity } from "@/lib/opportunities";
import { samplePlaces, type Place } from "@/lib/places";
import { API_BASE } from "./config";
import { extractList, isObj, normalizeOpportunity, normalizePlace } from "./normalize";

/**
 * SERVER side data layer (used by the pages when they are built / refreshed).
 *
 * With NEXT_PUBLIC_API_BASE_URL set the app calls:
 *   GET {base}/places            list of places
 *   GET {base}/places/{id}       one place
 *   GET {base}/opportunities     economic opportunities
 * Without it (or if a call fails) the built-in sample data is used.
 * The browser-side calls (category filter, suggestions) are in ./client.ts.
 */
const REVALIDATE_SECONDS = 300;

async function request(path: string): Promise<unknown | null> {
  if (!API_BASE) return null;
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: REVALIDATE_SECONDS },
      signal: AbortSignal.timeout(4000),
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export async function getPlaces(): Promise<Place[]> {
  const list = extractList(await request("/places"));
  if (list) {
    const places = list.map(normalizePlace).filter((p): p is Place => p !== null);
    if (places.length > 0) return places;
  }
  return samplePlaces;
}

export async function getPlace(id: string): Promise<Place | null> {
  const json = await request(`/places/${encodeURIComponent(id)}`);
  const fromApi = normalizePlace(isObj(json) && isObj(json.data) ? json.data : json);
  if (fromApi) return fromApi;
  return samplePlaces.find((p) => p.id === id) ?? null;
}

export async function getOpportunities(): Promise<Opportunity[]> {
  const list = extractList(await request("/opportunities"));
  if (list) {
    const items = list.map(normalizeOpportunity).filter((o): o is Opportunity => o !== null);
    if (items.length > 0) return items;
  }
  return sampleOpportunities;
}
