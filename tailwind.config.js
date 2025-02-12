/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./templates/**/*.html",
      "./static/**/*.js",
      "./node_modules/flowbite/**/*.js"
    ],
    darkMode: 'class',
    future: {
      hoverOnlyWhenSupported: true,
      respectDefaultRingColorOpacity: true,
      disableColorOpacityUtilitiesByDefault: true,
      colorDeduplication: true,
    },
    experimental: {
      optimizeUniversalDefaults: true,
      colorMatrix: true,
    },
    theme: {
      extend: {
        // Niestandardowe breakpointy dla RWD
        screens: {
          'xs': '475px',
          '3xl': '1600px',
        },
        // Własne wartości spacing dla precyzyjnego pozycjonowania
        spacing: {
          '18': '4.5rem',
          '72': '18rem',
          '84': '21rem',
          '96': '24rem',
        },
        // Niestandardowe cienie
        boxShadow: {
          'soft': '0 3px 10px rgba(0,0,0,0.05)',
          'card': '0 2px 4px rgba(0,0,0,0.06), 0 4px 6px rgba(0,0,0,0.1)',
          'nav': '0 4px 12px rgba(0,0,0,0.08)',
        },
        // Własne animacje
        animation: {
          'spin-slow': 'spin 3s linear infinite',
          'bounce-slow': 'bounce 3s infinite',
          'fade-in': 'fadeIn 0.5s ease-in',
        },
        keyframes: {
          fadeIn: {
            '0%': { opacity: '0' },
            '100%': { opacity: '1' },
          }
        },
        // Niestandardowe wartości border-radius
        borderRadius: {
          'xl': '1rem',
          '2xl': '2rem',
          '4xl': '4rem',
        },
        // Własne wartości z-index
        zIndex: {
          '60': '60',
          '70': '70',
          '80': '80',
          '90': '90',
          '100': '100',
        },
        // Niestandardowe wartości transition
        transitionDuration: {
          '400': '400ms',
          '2000': '2000ms',
        },
        // Własne fonty (jeśli używamy)
        fontFamily: {
          'sans': ['Inter', 'system-ui', 'sans-serif'],
          'display': ['Poppins', 'system-ui', 'sans-serif'],
        },
      },
    },
    plugins: [
      require('flowbite/plugin')
    ],
}