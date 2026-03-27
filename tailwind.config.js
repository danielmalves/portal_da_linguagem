module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Manrope", "sans-serif"],
        display: ["Fraunces", "serif"],
      },
      keyframes: {
        globeSpin: {
          "0%": { transform: "rotateY(0deg)" },
          "100%": { transform: "rotateY(360deg)" },
        },
        globeFloat: {
          "0%, 100%": { transform: "translateY(0px) translateX(0px)" },
          "50%": { transform: "translateY(-8px) translateX(4px)" },
        },
      },
      animation: {
        "globe-spin": "globeSpin 72s linear infinite",
        "globe-float": "globeFloat 9s ease-in-out infinite",
      },
      boxShadow: {
        soft: "0 24px 60px rgba(25, 28, 29, 0.12)",
      },
    },
  },
  plugins: [],
}
