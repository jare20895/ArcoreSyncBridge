import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Light Mode
        light: {
          bg: '#F5F4F2',
          surface: '#FFFFFF',
          primary: '#1B4F72',
          accent: '#D97706',
          success: '#2F855A',
          warning: '#B45309',
          danger: '#B91C1C',
          text: {
            primary: '#1F2933',
            secondary: '#52606D',
          }
        },
        // Dark Mode
        dark: {
          bg: '#0F1720',
          surface: '#141E2A',
          primary: '#7FB3D5',
          accent: '#F4B266',
          success: '#6EE7B7',
          warning: '#FBBF24',
          danger: '#F87171',
          text: {
            primary: '#E2E8F0',
            secondary: '#94A3B8',
          }
        }
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui'],
        secondary: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      spacing: {
        'sidebar': '260px',
        'sidebar-collapsed': '72px',
        'header': '64px',
      }
    },
  },
  plugins: [],
}
export default config