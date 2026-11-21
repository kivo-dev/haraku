import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { DiscoverBrowser } from "@/components/discover/DiscoverBrowser";
import { getCategories, getPlaces } from "@/lib/api/places";

export const revalidate = 300;

export default async function DiscoverPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [places, categories] = await Promise.all([getPlaces(), getCategories()]);

  return (
    <Suspense fallback={null}>
      <DiscoverBrowser places={places} categories={categories} />
    </Suspense>
  );
}
