/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
      colors: {
        // --- Light-First Surfaces ---
        app:        '#f8fafc', // Off-white application background
        panel:      '#ffffff', // Clean white panel surface
        surface:    '#f1f5f9', // Muted surface / table header
        
        // --- Navy & Saffron Accents ---
        navy: {
          DEFAULT: '#0f172a',
          800:     '#1e293b',
          900:     '#0f172a',
        },
        saffron: {
          DEFAULT: '#d97706',
          dark:    '#b45309',
          light:   '#fef3c7',
        },

        // --- Restrained Institutional Borders ---
        border:     '#e2e8f0',
        'border-subtle': '#f1f5f9',

        // --- Text Hierarchy ---
        'text-primary':   '#0f172a', // Deep Navy/Slate
        'text-secondary': '#475569', // Slate sub-text
        'text-muted':     '#94a3b8', // Muted label text
        'text-mono':      '#1e293b',

        // --- Institutional Status Tokens ---
        status: {
          confirmed:   '#166534', // Restrained emerald
          confirmedBg: '#dcfce7',
          active:      '#1d4ed8', // Restrained blue
          activeBg:    '#dbeafe',
          warning:     '#b45309', // Restrained saffron/amber
          warningBg:   '#fef3c7',
          critical:    '#b91c1c', // Restrained red
          criticalBg:  '#fee2e2',
          deferred:    '#4c1d95', // Purple
          deferredBg:  '#f3e8ff',
          closed:      '#475569', // Slate
          closedBg:    '#f1f5f9',
        },

        // --- Entity Type Indicators ---
        'entity-person':    '#2563eb',
        'entity-org':       '#d97706',
        'entity-device':    '#7c3aed',
        'entity-phone':     '#059669',
        'entity-financial': '#b45309',
        'entity-vehicle':   '#dc2626',
        'entity-source':    '#475569',
      },
      borderRadius: {
        DEFAULT: '4px',
        'sm':    '2px',
        'md':    '4px',
        'lg':    '6px',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        panel:  '0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
};

