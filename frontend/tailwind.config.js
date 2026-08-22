/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        border:      "hsl(214, 32%, 91%)",
        background:  "hsl(0, 0%, 100%)",
        foreground:  "hsl(222, 47%, 11%)",
        card: {
          DEFAULT:    "hsl(0, 0%, 100%)",
          foreground: "hsl(222, 47%, 11%)",
        },
        primary: {
          DEFAULT:    "hsl(221, 83%, 53%)",
          foreground: "hsl(210, 40%, 98%)",
        },
        secondary: {
          DEFAULT:    "hsl(210, 40%, 96%)",
          foreground: "hsl(222, 47%, 11%)",
        },
        muted: {
          DEFAULT:    "hsl(210, 40%, 96%)",
          foreground: "hsl(215, 16%, 47%)",
        },
        accent: {
          DEFAULT:    "hsl(210, 40%, 96%)",
          foreground: "hsl(222, 47%, 11%)",
        },
        destructive: {
          DEFAULT:    "hsl(0, 84%, 60%)",
          foreground: "hsl(210, 40%, 98%)",
        },
      },
    },
  },
  plugins: [],
};
