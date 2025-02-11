/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.{html, js}",
    'node_modules/preline/dist/*.js',
    '../static/js/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('preline/plugin'),
  ],
}

