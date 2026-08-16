---
name: FinSight Intelligence
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c6c5d5'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908f9e'
  outline-variant: '#454653'
  surface-tint: '#bdc2ff'
  primary: '#bdc2ff'
  on-primary: '#131e8c'
  primary-container: '#818cf8'
  on-primary-container: '#101b8a'
  inverse-primary: '#4953bc'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb2b7'
  on-tertiary: '#67001b'
  tertiary-container: '#ff5c72'
  on-tertiary-container: '#630019'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e0e0ff'
  primary-fixed-dim: '#bdc2ff'
  on-primary-fixed: '#000767'
  on-primary-fixed-variant: '#2f3aa3'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdadb'
  tertiary-fixed-dim: '#ffb2b7'
  on-tertiary-fixed: '#40000d'
  on-tertiary-fixed-variant: '#92002a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1440px
  gutter: 20px
---

## Brand & Style

The design system is engineered for high-stakes financial intelligence. It balances the precision of data-heavy interfaces with the fluid, intuitive nature of AI-driven insights. The aesthetic is **Sophisticated Minimalism**: a dark-mode first experience that uses depth and color selectively to guide the eye toward critical market movements and AI forecasts.

The brand personality is **Credible and Intelligent**. It avoids the chaotic density of traditional trading terminals in favor of a "Focus-First" philosophy—where whitespace is a tool for clarity, and premium finishes like subtle borders and soft blurs evoke a sense of digital craftsmanship. The target audience includes high-net-worth individuals and professional analysts who require high data density without cognitive overload.

## Colors

The palette is built on a foundation of deep, professional tones to ensure long-session legibility and a premium feel.

- **Foundational Tones:** The background uses a deep navy-charcoal to minimize eye strain. Surfaces are layered using a slightly lighter navy to create a hierarchy of information containers.
- **Accents & Semantics:** 
    - **Indigo (#818CF8):** Reserved for AI-driven insights, forecasting, and primary actions. It represents the "Intelligence" layer.
    - **Emerald (#10B981):** Represents growth, profit, and positive market trends.
    - **Rose (#F43F5E):** Used for losses, risks, and critical alerts.
    - **Orange (#F59E0B):** Signals warnings or pending states.
- **Contrast:** Borders use a low-contrast steel blue to define shapes without creating visual noise. Text is strictly tiered between stark white for headings and muted slate for metadata.

## Typography

This design system utilizes **Inter** for all UI and editorial content due to its exceptional legibility in dark mode and professional grit. For financial figures, tickers, and technical data points, **JetBrains Mono** is introduced to provide a distinct "technical" feel and ensure tabular numbers align perfectly.

- **Headlines:** Use tight letter-spacing and bold weights to command attention.
- **Data Display:** Large numerical values (portfolio totals, percentage changes) should use `display-md` or `display-lg` to act as visual anchors.
- **Labels:** Small caps with increased tracking are used for secondary category labels to distinguish them from interactive body text.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for desktop, transitioning to a **4-column grid** for mobile. 

- **Rhythm:** A strict 4px baseline grid ensures vertical consistency. 
- **Density:** While the design is "high-density," this is achieved through purposeful grouping of data within cards rather than crowding the entire screen. 
- **Structure:**
    - **Desktop:** Sidebar navigation (fixed 260px) with a fluid content area.
    - **Tablet:** Collapsed rail navigation with increased margins (32px).
    - **Mobile:** Bottom tab bar navigation; margins reduced to 16px to maximize data visualization real estate.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and **Subtle Outlines** rather than heavy shadows.

- **Level 0 (Background):** #0F172A - The lowest plane.
- **Level 1 (Cards/Sections):** #1E293B - Raised slightly with a 1px solid border (#334155).
- **Level 2 (Modals/Popovers):** #26334D - Higher contrast background with a soft, diffused shadow (0px 20px 25px -5px rgba(0,0,0,0.4)).
- **Glassmorphism:** Use `backdrop-filter: blur(12px)` for sticky headers and sidebars to maintain a sense of space and context while scrolling.

## Shapes

The shape language is **Rounded**, signifying a modern, approachable fintech experience. 

- **Standard Elements:** Buttons, input fields, and small widgets use a 0.5rem (8px) radius.
- **Containers:** Dashboard cards and main content areas use `rounded-lg` (16px) to create a distinct soft-frame effect against the dark background.
- **Interactive States:** Segmented controls and pills use a fully rounded (pill) radius to distinguish them from structural containers.

## Components

- **Buttons:** Primary buttons use the Indigo accent with white text. Secondary buttons are "Ghost" style—transparent background with a #334155 border and white text. Use 12px horizontal padding for a compact, professional look.
- **Horizontal Ticker:** A dedicated component for real-time market data. Uses a 1px top/bottom border, JetBrains Mono font, and a subtle scrolling animation.
- **Cards:** The primary container. Must include a title header with `label-caps` and a 1px bottom divider. Background is #1E293B.
- **Segmented Controls:** Used for switching timeframes (1D, 1W, 1M, 1Y). These should have a subtle dark-grey track (#0F172A) and a slightly raised active state.
- **Input Fields:** Darker than the surface color to create an "inset" feel. Borders should glow Indigo (#818CF8) only when focused.
- **Data Visualizations:** Charts should use a 2px stroke width. Success (Emerald) and Danger (Rose) should be used for trend lines. AI-predicted areas should use a dashed stroke with an Indigo outer glow.
- **Chips/Badges:** Small, low-saturation backgrounds (e.g., 10% opacity Emerald) with high-saturation text for status indicators.