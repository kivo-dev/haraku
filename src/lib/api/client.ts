import type { Opportunity } from "@/lib/opportunities";
import type { Place } from "@/lib/places";
import { API_BASE } from "./config";
import { extractList, normalizeOpportunity, normalizePlace } from "./normalize";

/**
 * BROWSER side data layer: calls made while the user is using the app.
 * Always fresh (no cache). The backend must allow requests from the app's address (CORS).
 *
 *   GET {base}/places?category=nature&q=...      places of one category / matching a search
 *   GET {base}/suggestions?limit=6               "Our suggestions": the backend decides what to
 *                                                suggest (and may return something new each time)
 *   GET {base}/opportunities?sector=trade        economic opportunities of one sector
 *
 * Every function throws if the call fails; the screens then fall back to the sample data.
 */
type Params = Record<string, string | number | undefined>;

const backendCategory: Record<string, string> = {
  attractions: "history",
  nature_adventure: "nature",
  public_services: "services",
};

async function getJson(path: string, params: Params, signal?: AbortSignal): Promise<unknown> {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") query.set(k, String(v));
  const qs = query.toString();
  const res = await fetch(`${API_BASE}${path}${qs ? `?${qs}` : ""}`, {
    signal,
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

const places = (json: unknown) => (extractList(json) ?? []).map(normalizePlace).filter((p): p is Place => p !== null);

export async function fetchPlaces(p: {
  category?: string;
  q?: string;
  signal?: AbortSignal;
}): Promise<Place[]> {
  const category = p.category
    ? backendCategory[p.category] ?? p.category
    : undefined;

  return places(
    await getJson("/places", { category, q: p.q }, p.signal)
  );
}


export async function fetchSuggestions(p: { limit?: number; signal?: AbortSignal } = {}): Promise<Place[]> {
  return places(await getJson("/suggestions", { limit: p.limit ?? 6 }, p.signal));
}

export async function fetchOpportunities(p: { sector?: string; signal?: AbortSignal }): Promise<Opportunity[]> {
  const list = extractList(await getJson("/opportunities", { sector: p.sector }, p.signal)) ?? [];
  return list.map(normalizeOpportunity).filter((o): o is Opportunity => o !== null);
}
