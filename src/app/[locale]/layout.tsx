import type { Metadata, Viewport } from "next";
import { notFound } from "next/navigation";
import { Lalezar, Poppins } from "next/font/google";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { routing } from "@/i18n/routing";
import { ServiceWorkerRegister } from "@/components/layout/ServiceWorkerRegister";
import { getDirection } from "@/lib/dir";
import "@/styles/globals.css";

// Latin letters and digits; Persian text falls through to Vazirmatn (see tailwind.config.ts).
const latin = Poppins({ subsets: ["latin"], weight: ["300", "400", "500", "600", "700"], variable: "--font-latin", display: "swap" });

// Fancy display font: used only for the big headlines and the top menu (class "font-display").
const display = Lalezar({ subsets: ["arabic", "latin"], weight: "400", variable: "--font-display", display: "swap" });

type Props = { children: React.ReactNode; params: Promise<{ locale: string }> };

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#12332c",
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: Omit<Props, "children">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Meta" });
  return {
    title: t("title"),
    description: t("description"),
    applicationName: "HARAKO",
    icons: {
      icon: [{ url: "/favicon.png", type: "image/png" }, { url: "/icon-192.png", sizes: "192x192", type: "image/png" }],
      apple: "/apple-touch-icon.png",
    },
    appleWebApp: { capable: true, title: "HARAKO", statusBarStyle: "black-translucent" },
  };
}

// Root layout: owns <html>/<body> so lang and dir follow the locale.
export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);

  return (
    <html lang={locale} dir={getDirection(locale)} className={`${latin.variable} ${display.variable}`}>
      <body>
        <NextIntlClientProvider>{children}</NextIntlClientProvider>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
