import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm paper cream: page background and quiet surfaces (matches the paper scene)
        mist: {
          50: "#fbf6ea",
          100: "#f7eedc",
          200: "#f1e4cb",
          300: "#e6d3b0",
        },
        // Deep green for text on light, dark buttons, nav
        forest: {
          50: "#eef6f2",
          100: "#d5eadf",
          200: "#aad4c1",
          500: "#2a8a70",
          600: "#1b6b57",
          700: "#165a49",
          800: "#184a3d",
          900: "#12332c",
          950: "#0b221d",
        },
        // The single bright accent: primary actions and active states
        lime: {
          300: "#dfec7a",
          400: "#d0e24a",
          500: "#c3d62f",
          600: "#a9bb1d",
        },
        // Sunrise haze, used only for light glows on the landing hero
        dawn: { 100: "#fff6ea", 200: "#f9e2c8", 300: "#f0c89d" },
        ink: { 400: "#8a938e", 500: "#5b6560", 700: "#2a332f", 900: "#141a17" },
      },
      fontFamily: {
        // Latin glyphs come from Poppins (next/font), Persian from Vazirmatn.
        // Fancy headline font (loaded in app/[locale]/layout.tsx)
        display: ["var(--font-display)", "Vazirmatn", "system-ui", "sans-serif"],
        sans: ["var(--font-latin)", "Vazirmatn", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      borderRadius: { "4xl": "2rem", "5xl": "2.5rem" },
      boxShadow: {
        soft: "0 14px 34px -16px rgb(18 51 44 / 0.35)",
        float: "0 18px 40px -14px rgb(11 34 29 / 0.55)",
      },
    },
  },
  plugins: [],
};

export default config;
