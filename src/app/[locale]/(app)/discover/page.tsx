import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { DiscoverBrowser } from "@/components/discover/DiscoverBrowser";
import { getPlaces } from "@/lib/api/places";

// Refresh the list from the API every 5 minutes (falls back to sample data).
export const revalidate = 300;

export default async function DiscoverPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const places = await getPlaces();

  return (
    // Suspense is required because the browser reads ?q= from the URL.
    <Suspense fallback={null}>
      <DiscoverBrowser places={places} />
    </Suspense>
  );
}
