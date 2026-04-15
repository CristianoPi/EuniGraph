import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#18181b",
      },
      boxShadow: {
        panel: "0 18px 50px rgba(24, 24, 27, 0.07)",
      },
      backgroundImage: {
        "shell-glow": "radial-gradient(circle at top right, rgba(245, 158, 11, 0.1), transparent 26%)",
      },
      fontFamily: {
        sans: ["Space Grotesk", "Avenir Next", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
