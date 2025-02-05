module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Ini memastikan Tailwind menganalisis file di folder src
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')], // Tambahkan plugin jika digunakan
  daisyui: {
    themes: ["light"], // Pilih tema DaisyUI jika digunakan
  },
};
