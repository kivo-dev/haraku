/**
 * IMAGE SLOTS — the single place that says "which photo goes where".
 *
 * Drop your own file at the path shown in `src` (inside /public) and it appears
 * automatically. Until the file exists, a designed placeholder illustration is shown,
 * so nothing breaks. Full list with sizes and photo ideas: IMAGE_GUIDE.md
 */
export type ImageSlot = {
  /** URL path (file lives in /public + this path) */
  src: string;
  /** Recommended pixel size (width × height) */
  size: string;
  /** What the photo should show */
  hint: string;
  /** Where it appears in the app */
  where: string;
};

export const imageSlots = {
  landingHero: {
    src: "/images/landing-hero.jpg",
    size: "2400×1500",
    hint: "Wide, misty mountain or valley at sunrise. Bright/hazy upper half, darker ground at the bottom.",
    where: "Landing page (/): full-screen background on desktop and phone",
  },
  landingHeroMobile: {
    src: "/images/landing-hero-mobile.jpg",
    size: "1080×1920",
    hint: "Tall (portrait) photo: dark foggy forest or mountain. Text sits on the lower half, so keep that part dark and calm.",
    where: "Landing page (/) on phones",
  },
  soonMap: {
    src: "/images/soon-map.jpg",
    size: "1200×800",
    hint: "Landscape seen from above, a road or river winding through it.",
    where: "Map tab (until the real map is added)",
  },
  soonAssistant: {
    src: "/images/soon-assistant.jpg",
    size: "1200×800",
    hint: "Calm forest or trail, soft light.",
    where: "Assistant tab (until the assistant is added)",
  },
  soonRoute: {
    src: "/images/soon-route.jpg",
    size: "1200×800",
    hint: "A path or road disappearing into hills.",
    where: "Route tab (until routing is added)",
  },
} as const satisfies Record<string, ImageSlot>;

/** Main photo of a place: `/images/places/<place-id>.jpg` (1200×900, 4:3). */
export function placeImageSrc(placeId: string, apiImage?: string): string {
  return apiImage ?? `/images/places/${placeId}.jpg`;
}

/** Optional extra photos on the place page: `/images/places/<place-id>-2.jpg`, `-3.jpg` (1200×900). */
export function placeGallerySrc(placeId: string): string[] {
  return [2, 3].map((n) => `/images/places/${placeId}-${n}.jpg`);
}
