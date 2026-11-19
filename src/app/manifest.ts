import type { MetadataRoute } from "next";

// Served at /manifest.webmanifest. Default locale is Persian, so the installed
// app opens on the Persian Discover page.
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/fa/discover",
    name: "هراکو — کاوش منطقه آزاد ماکو",
    short_name: "هراکو",
    description: "پلتفرم هوشمند گردشگری منطقه آزاد ماکو، آذربایجان غربی.",
    lang: "fa",
    dir: "rtl",
    start_url: "/fa/discover",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#d6e7da",
    theme_color: "#12332c",
    categories: ["travel", "navigation"],
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
