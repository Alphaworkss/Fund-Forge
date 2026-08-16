import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "surface-dim": "#0b1326",
        "surface-container-lowest": "#060e20",
        "surface-container-low": "#131b2e",
        "surface-container": "#171f33",
        "surface-container-high": "#222a3d",
        "surface-container-highest": "#2d3449",
        "surface-bright": "#31394d",
        "surface-variant": "#2d3449",
        "surface": "#0b1326",
        "background": "#0b1326",
        "on-surface": "#dae2fd",
        "on-surface-variant": "#c6c5d5",
        "on-background": "#dae2fd",
        "outline": "#908f9e",
        "outline-variant": "#454653",
        "primary": "#bdc2ff",
        "primary-container": "#818cf8",
        "on-primary": "#131e8c",
        "on-primary-container": "#101b8a",
        "secondary": "#4edea3",
        "secondary-container": "#00a572",
        "on-secondary": "#003824",
        "tertiary": "#ffb2b7",
        "tertiary-container": "#ff5c72",
        "error": "#ffb4ab",
        "error-container": "#93000a",
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "sm": "0.25rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1.0rem",
        "full": "9999px",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
      },
      spacing: {
        "xs": "8px",
        "sm": "12px",
        "md": "16px",
        "lg": "24px",
        "xl": "40px",
        "gutter": "20px",
      }
    },
  },
  plugins: [],
};
export default config;
