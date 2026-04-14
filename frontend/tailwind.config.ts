import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#102432",
        mist: "#edf3ef",
        ember: "#c6653d",
        pine: "#0f4c5c",
        moss: "#52796f",
        sand: "#f5efe6",
      },
      boxShadow: {
        panel: "0 24px 60px rgba(16, 36, 50, 0.12)",
      },
      backgroundImage: {
        "shell-glow": "radial-gradient(circle at top left, rgba(198, 101, 61, 0.16), transparent 32%), radial-gradient(circle at top right, rgba(15, 76, 92, 0.14), transparent 28%)",
      },
      fontFamily: {
        sans: ["Space Grotesk", "Avenir Next", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
