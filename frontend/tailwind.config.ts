import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        muted: "#647084",
        line: "#E5EAF1",
        surface: "#F6F8FB",
        brand: {
          50: "#EEF6FF",
          100: "#D9EAFF",
          500: "#2268D8",
          600: "#1B57B8",
          700: "#164896"
        },
        success: "#188B5B",
        warning: "#B76E00",
        danger: "#C2413A"
      },
      boxShadow: {
        soft: "0 18px 45px rgba(20, 32, 53, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
