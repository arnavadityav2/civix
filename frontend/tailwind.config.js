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
        // IBM Plex Sans: primary institutional sans-serif
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        // IBM Plex Mono: case IDs, timestamps, technical metadata only
        mono: ['"IBM Plex Mono"', 'Consolas', 'monospace'],
      },
      colors: {
        // ─── CIVIX ENVIRONMENT (Dark Navy / Blue-Black) ───────────────────────
        // The application container. Not pure black — sophisticated tonal variation.
        'civix-bg':        '#0a0e1a', // Deepest background (outer shell)
        'civix-surface':   '#0f1623', // Primary surface (panels, cards)
        'civix-surface-2': '#141c2e', // Raised surface (panel headers, sidebars)
        'civix-surface-3': '#1a2440', // Elevated surface (hover states, selected rows)
        'civix-surface-4': '#1f2d50', // Highest elevation (active state)

        // ─── BORDERS (Institutional, not glowing) ───────────────────────────
        'civix-border':         '#1e2d4a', // Standard border
        'civix-border-subtle':  '#162035', // Hairline / de-emphasized border
        'civix-border-strong':  '#2a3d62', // Emphasis border (active panel)

        // ─── TEXT HIERARCHY ─────────────────────────────────────────────────
        'civix-text-primary':   '#e8edf5', // Primary information (white/near-white)
        'civix-text-secondary': '#8fa3c0', // Secondary labels
        'civix-text-muted':     '#4a6080', // De-emphasized / metadata
        'civix-text-mono':      '#7eb8d4', // Monospace technical identifiers

        // ─── BLUE: Structure, navigation, analytical context ────────────────
        'civix-blue': {
          DEFAULT: '#2d7dd2', // Primary blue
          light:   '#4a9ee8', // Active / hover
          dark:    '#1a5fa0', // Deep blue for borders/accents
          subtle:  '#0d2a4a', // Blue tinted surface
          muted:   '#1a4070', // Blue border on dark
        },

        // ─── RED: Investigative urgency, critical signals ────────────────────
        'civix-red': {
          DEFAULT: '#c0392b', // Primary red
          light:   '#e74c3c', // Alert / high-priority
          dark:    '#922b21', // Deep red for borders
          subtle:  '#2d0a0a', // Red-tinted surface
          muted:   '#5c1a1a', // Red border on dark
        },

        // ─── YELLOW / GOLD: Institutional identity, priority ─────────────────
        'civix-gold': {
          DEFAULT: '#c8a84b', // Primary institutional gold
          light:   '#e8c860', // Lighter gold accent
          dark:    '#9a7a30', // Deep gold border
          subtle:  '#1e1600', // Gold-tinted surface
          muted:   '#3a2a00', // Gold border on dark
        },

        // ─── GREEN: Verified / confirmed states ONLY ─────────────────────────
        'civix-green': {
          DEFAULT: '#1e8449', // Verified green
          light:   '#27ae60', // Confirmed active
          dark:    '#166035', // Deep green border
          subtle:  '#001a0d', // Green-tinted surface
          muted:   '#0a3d1f', // Green border on dark
        },

        // ─── SEMANTIC STATUS TOKENS ──────────────────────────────────────────
        // These MUST replace the old status.* tokens that used purple.
        status: {
          // ACTIVE investigation = blue (system structure)
          active:       '#2d7dd2',
          activeBg:     '#0d2a4a',
          activeBorder: '#1a4070',
          // CRITICAL/HIGH = red (urgency)
          critical:     '#c0392b',
          criticalBg:   '#2d0a0a',
          criticalBorder:'#5c1a1a',
          // PRIORITY/REVIEW = gold (institutional attention)
          warning:      '#c8a84b',
          warningBg:    '#1e1600',
          warningBorder:'#3a2a00',
          // CONFIRMED/VERIFIED = green
          confirmed:    '#1e8449',
          confirmedBg:  '#001a0d',
          confirmedBorder:'#0a3d1f',
          // CLOSED/DEFERRED = neutral slate (no purple)
          closed:       '#4a6080',
          closedBg:     '#0f1623',
          closedBorder: '#1e2d4a',
          // DEFERRED: formerly purple — now gold/review state
          deferred:     '#c8a84b',
          deferredBg:   '#1e1600',
          deferredBorder:'#3a2a00',
        },

        // ─── ENTITY TYPE INDICATORS (dark-adjusted) ──────────────────────────
        'entity-person':    '#2d7dd2', // Blue
        'entity-org':       '#c8a84b', // Gold (replaces amber/orange)
        'entity-device':    '#2d7dd2', // Blue (replaces purple — FORBIDDEN)
        'entity-phone':     '#1e8449', // Green
        'entity-financial': '#c8a84b', // Gold
        'entity-vehicle':   '#c0392b', // Red
        'entity-source':    '#4a6080', // Muted slate

        // ─── LEGACY REMOVAL ──────────────────────────────────────────────────
        // These old tokens are intentionally removed:
        // app, panel, surface (old light SaaS tokens)
        // navy.* (replaced by civix-surface-*)
        // saffron.* (replaced by civix-gold.*)
        // border/border-subtle (replaced by civix-border-*)
        // text-primary/secondary/muted/mono (replaced by civix-text-*)
      },

      // ─── BORDER RADIUS: institutional sharp edges ────────────────────────
      // CIVIX uses minimal rounding — it's a professional workstation, not a SaaS app.
      borderRadius: {
        DEFAULT: '2px',
        'sm':    '1px',
        'md':    '2px',
        'lg':    '4px',
        'xl':    '6px',
      },

      // ─── SHADOWS: depth via tonal variation, not glow ────────────────────
      boxShadow: {
        'civix-sm':  '0 1px 3px 0 rgba(0, 0, 0, 0.5)',
        'civix-md':  '0 4px 12px 0 rgba(0, 0, 0, 0.4)',
        'civix-lg':  '0 8px 24px 0 rgba(0, 0, 0, 0.5)',
        'civix-inset': 'inset 0 1px 0 rgba(255, 255, 255, 0.04)',
      },
    },
  },
  plugins: [],
};
