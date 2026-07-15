import type { Config } from "tailwindcss";

// Design tokens for Sketch2Code AI
// ink   -> near-black canvas/panel scale (the "drawing surface")
// violet -> primary brand/AI accent (the electric line that turns sketch into code)
// mint  -> success / "code generated" signal color (terminal-esque)
// paper -> warm off-white text, evokes sketch paper rather than clinical white
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0A0B10",
          900: "#12141C",
          800: "#1B1E29",
          700: "#262A3A",
          600: "#363B52",
        },
        violet: {
          400: "#9A8CFF",
          500: "#7C5CFF",
          600: "#6444E6",
        },
        mint: {
          400: "#2EE6A6",
          500: "#17C98C",
        },
        paper: {
          100: "#EDEBE6",
          300: "#B8B6C4",
          500: "#7D7B8C",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(to right, rgba(237,235,230,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(237,235,230,0.04) 1px, transparent 1px)",
        "sketch-glow":
          "radial-gradient(circle at 50% 0%, rgba(124,92,255,0.25), transparent 60%)",
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0,0,0,0.35)",
        "glow-violet": "0 0 40px rgba(124,92,255,0.35)",
      },
      backdropBlur: {
        xs: "2px",
      },
      keyframes: {
        "dash-flow": {
          to: { strokeDashoffset: "-40" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "dash-flow": "dash-flow 1.2s linear infinite",
        "fade-up": "fade-up 0.6s ease-out both",
      },
    },
  },
  plugins: [],
} satisfies Config;
