import { setRequestLocale } from "next-intl/server";
import { OpportunitiesBrowser } from "@/components/discover/OpportunitiesBrowser";
import { getOpportunities } from "@/lib/api/places";

// Refresh the list from the API every 5 minutes.
export const revalidate = 300;

export default async function OpportunitiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { items, failed } = await getOpportunities();
  return <OpportunitiesBrowser items={items} loadFailed={failed} />;
}
