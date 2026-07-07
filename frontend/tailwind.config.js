/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#FAF9F6",
        surface: "#FFFFFF",
        ink: "#14181A",
        muted: "#63706A",
        line: "#E5E3DD",
        pine: {
          DEFAULT: "#0D4F45",
          dark: "#082F29",
          light: "#E4EFEB",
        },
        gold: {
          DEFAULT: "#B8862E",
          light: "#F7EEDD",
        },
        status: {
          ok: "#1F8A5F",
          okBg: "#E7F5EE",
          warn: "#B8862E",
          warnBg: "#FBF1E1",
          danger: "#C0392B",
          dangerBg: "#FBEAE6",
          pending: "#7C8880",
          pendingBg: "#EEF0EE",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,24,26,0.04), 0 8px 24px -12px rgba(20,24,26,0.10)",
        cardHover: "0 2px 4px rgba(20,24,26,0.05), 0 16px 32px -12px rgba(20,24,26,0.14)",
      },
      borderRadius: {
        xl2: "1.1rem",
      },
    },
  },
  plugins: [],
};

