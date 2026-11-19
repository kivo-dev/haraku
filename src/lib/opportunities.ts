import { Factory, Mountain, Sprout, Truck, type LucideIcon } from "lucide-react";
import type { LocalizedText } from "@/lib/places";

export const sectorKeys = ["trade", "industry", "agriculture", "tourism"] as const;
export type SectorKey = (typeof sectorKeys)[number];

export const sectorIcons: Record<SectorKey, LucideIcon> = {
  trade: Truck,
  industry: Factory,
  agriculture: Sprout,
  tourism: Mountain,
};

/** Colour mood of the placeholder illustration, per sector. */
export const sectorArt: Record<SectorKey, "forest" | "dawn" | "fog"> = {
  trade: "fog",
  industry: "dawn",
  agriculture: "forest",
  tourism: "forest",
};

/** An economic opportunity in the city. Everything except id/sector/title is optional. */
export type Opportunity = {
  id: string;
  sector: SectorKey;
  title: LocalizedText;
  summary: LocalizedText;
  /** Full image URL from the API. When missing, /images/opportunities/<id>.jpg is used. */
  image?: string;
  /** "sample" = built-in placeholder, "api" = came from the backend. */
  source: "sample" | "api";
};

/** Image of an opportunity: `/images/opportunities/<id>.jpg` (1200×900). */
export function opportunityImageSrc(id: string, apiImage?: string): string {
  return apiImage ?? `/images/opportunities/${id}.jpg`;
}

// PLACEHOLDERS ONLY: no real facts. They disappear as soon as the API returns data.
export const sampleOpportunities: Opportunity[] = (
  [
    ["sample-trade", "trade", "فرصت نمونه در تجارت و ترانزیت", "Sample trade and transit opportunity"],
    ["sample-industry", "industry", "فرصت نمونه در صنعت", "Sample industry opportunity"],
    ["sample-agriculture", "agriculture", "فرصت نمونه در کشاورزی", "Sample agriculture opportunity"],
    ["sample-tourism", "tourism", "فرصت نمونه در گردشگری", "Sample tourism opportunity"],
  ] as const
).map(([id, sector, fa, en]) => ({
  id,
  sector,
  title: { fa, en },
  summary: {
    fa: "شرح این فرصت بعداً از سرور (API) می‌آید.",
    en: "The description of this opportunity will come from the server (API).",
  },
  source: "sample" as const,
}));
