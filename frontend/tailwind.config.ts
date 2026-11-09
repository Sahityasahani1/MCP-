import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brut: {
          red: "#FF0000",
          blue: "#0000FF",
          yellow: "#FFFF00",
          black: "#000000",
          white: "#FFFFFF",
          green: "#00FF00",
          magenta: "#FF00FF",
        },
      },
      boxShadow: {
        brut: "4px 4px 0 #000000",
        "brut-lg": "8px 8px 0 #000000",
        "brut-sm": "2px 2px 0 #000000",
      },
    },
  },
  plugins: [],
};
export default config;
