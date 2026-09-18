---
name: Calm & Simple Pet Recovery
colors:
  surface: '#fff8f6'
  surface-dim: '#dfd9d7'
  surface-bright: '#fff8f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9f2f1'
  surface-container: '#f3eceb'
  surface-container-high: '#ede7e5'
  surface-container-highest: '#e7e1e0'
  on-surface: '#1d1b1a'
  on-surface-variant: '#414941'
  inverse-surface: '#32302f'
  inverse-on-surface: '#f6efee'
  outline: '#727970'
  outline-variant: '#c1c9be'
  surface-tint: '#3a6843'
  primary: '#204e2b'
  on-primary: '#ffffff'
  primary-container: '#386641'
  on-primary-container: '#afe2b3'
  inverse-primary: '#a0d3a5'
  secondary: '#44664a'
  on-secondary: '#ffffff'
  secondary-container: '#c3e9c5'
  on-secondary-container: '#486a4e'
  tertiary: '#603d16'
  on-tertiary: '#ffffff'
  tertiary-container: '#7b542b'
  on-tertiary-container: '#ffcb9a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#bcefc0'
  primary-fixed-dim: '#a0d3a5'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#22502d'
  secondary-fixed: '#c6ecc8'
  secondary-fixed-dim: '#aad0ad'
  on-secondary-fixed: '#00210b'
  on-secondary-fixed-variant: '#2d4e33'
  tertiary-fixed: '#ffdcbd'
  tertiary-fixed-dim: '#f0bd8b'
  on-tertiary-fixed: '#2c1600'
  on-tertiary-fixed-variant: '#623f18'
  background: '#fff8f6'
  on-background: '#1d1b1a'
  surface-variant: '#e7e1e0'
typography:
  display:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: 0em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Nunito Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Nunito Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Nunito Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system is tailored for pet owners navigating post-operative care, rehabilitation, medication routines, and chronic wellness management. The emotional tone is reassuring, unhurried, empathetic, and gently optimistic. Pet health concerns can induce stress and cognitive overload; therefore, the interface deliberately eliminates clinical severity, diagnostic coldness, and overly technical jargon in favor of conversational clarity, comforting breathing room, and soft tactile presence.

The visual direction combines organic minimalism with tactile warmth:
- Generous, airy negative space to relieve cognitive burden.
- Gentle, grounding earth-derived neutrals rather than stark hospital whites.
- Softly contoured surfaces that evoke touchability, comfort, and domestic safety.
- Clear, plain-language guidance that breaks recovery timelines into manageable, bite-sized steps.

## Colors

The palette is rooted in gentle natural tones that soothe anxiety and provide clear visual wayfinding:

- **Primary (`#386641` - Deep Meadow Sage):** Serves as the primary anchor for key actions, primary navigation targets, and verified state milestones. It communicates vitality, natural healing, and stable care without medical sterility.
- **Secondary (`#7A9E7E` - Soft Willow):** Used for non-urgent supportive interactions, secondary button states, progress fills, and reassuring contextual badges.
- **Tertiary (`#D4A373` - Warm Honey Amber):** An empathetic accent for attention-demanding items like medication reminders, schedule highlights, and care-tip highlights, avoiding alarming high-intensity reds.
- **Neutral (`#736F6E` - Warm Slate):** Used to derive soft charcoal body text and balanced borders. The canvas background uses a soothing Warm Ivory (`#FAF7F2`) with container surfaces resting on Pure Linen (`#FFFFFF`) and Soft Oat (`#F3EFE6`).

## Typography

Typography prioritizes legibility, gentleness, and effortless scanning for tired caregivers. 

- **Headlines & Labels:** **Plus Jakarta Sans** brings balanced, open apertures and gentle curves that feel clean, contemporary, and warmly professional.
- **Body:** **Nunito Sans** provides open, rounded counters and high readability across long-form veterinary discharge notes, step-by-step instructions, and care logs.
- Never use full uppercase transforms in body copy or section warnings to avoid sounding alarmist or demanding. Keep tracking tight on large headings and natural on body text.

## Layout & Spacing

The layout is built upon an 8pt base grid implemented through a flexible 12-column structure on desktop/tablet and a single stacked column on mobile.

- **Mobile (< 768px):** 1-column stack, `1rem` page margin, and `1rem` column gutters. Cards span full width with internal `space-md` (`1rem`) to `space-lg` (`1.5rem`) padding.
- **Tablet (768px - 1024px):** 8-column layout, `1.5rem` outer margin, `1.5rem` gutters. Information is chunked into side-by-side modules (e.g., daily regimen alongside pet profile summaries).
- **Desktop (> 1024px):** 12-column layout maxing out at `1200px` container width, `3rem` outer margin, and `2rem` gutters.
- Vertical cadence relies heavily on generous spacing between distinct medical or recovery phases (`space-xl`), preventing visual crowding and allowing parents to focus on one action at a time.

## Elevation & Depth

This design system avoids heavy drop shadows and high-contrast borders that invoke industrial or technical interfaces. Instead, visual hierarchy is created through gentle, warm ambient shadows and tonal surface nesting:

- **Canvas Tier:** Soft tinted ivory (`#FAF7F2`) providing a restful base.
- **Surface Tier (Resting Cards):** Solid soft white (`#FFFFFF`) with an ambient feather shadow: `0 4px 20px -4px rgba(71, 64, 58, 0.05)` and a micro-border `1px solid #ECE7DE`.
- **Raised / Interactive Tier (Hover, Floating Action Bars):** Elevated surfaces receive an extended ambient lift: `0 10px 30px -6px rgba(71, 64, 58, 0.08)`, gently bringing the card closer without sharp boundaries.
- **Inset / Recessed Areas (Input fields, timeline tracks):** Soft oatmeal tint (`#F3EFE6`) with no shadow, communicating quiet containment.

## Shapes

The shape profile is set to level `2` (Rounded). This strikes a reassuring, organic balance that softens the interface without feeling overly juvenile:

- Standard cards, panels, and modals use `rounded-lg` (`1rem / 16px`).
- Feature cards and pet highlight banners utilize `rounded-xl` (`1.5rem / 24px`).
- Interactive controls such as primary buttons, tags, chips, and medication schedule status pills adopt fully rounded pill geometry (`9999px`) to invite gentle, confident touch interaction.

## Components

### Buttons
- **Primary:** Filled `#386641` with `#FFFFFF` text. Pill radius, minimum height 48px to accommodate effortless thumb tapping. Subtle hover brightness shift, no stark shadow jumps.
- **Secondary:** Tinted sage wash (`#EBF2EC`) with `#386641` text. Pill radius.
- **Ghost:** Transparent background with warm slate text (`#5A5553`) for cancel or secondary dismissal.

### Cards
- Enclosed with a `1px` border of `#ECE7DE`, pure white background, and `1rem` corner rounding.
- Generous internal padding (`1.5rem`). Key care cards feature an optional soft colored header strip (e.g., gentle sage or soft amber) to organize routines by morning, midday, and night.

### Chips & Badges
- Medication, symptom, and mood chips use fully rounded pill contours with soft pastel fills: Sage (`#EBF2EC`), Honey Oat (`#FAF0E4`), and Soft Slate (`#EDEAE5`).
- Text weight is set to `label-md` with gentle icon prefixes (such as paw prints, pill caps, or drop icons).

### Inputs & Form Elements
- **Text Inputs:** Outlined in `#DED7CB` against an `#FFFFFF` or `#F9F7F3` background with `0.75rem` (12px) rounding and 48px height. On focus, transition to `#386641` with a gentle 3px outer glow in `rgba(56, 102, 65, 0.15)`.
- **Checkboxes & Radios:** Rounded squares (6px radius) and circular radios with soft `#386641` active fills. Checkmarks use smooth, curved strokes.

### Lists & Activity Logs
- Timeline list items feature a connected vertical stem in `#E5DFD5` paired with circular status checkpoints.
- Avoid raw tabular data; present logs as conversational diary entries (e.g., "Mochi took 1 tablet with food at 8:30 AM").

### Recovery Progress Tracker
- A signature component displaying a smooth, uninterrupted horizontal bar with rounded ends, using `#7A9E7E` progress fill over an oatmeal track (`#EAE5DC`). Milestones are clearly annotated with reassuring encouraging labels (e.g., "Rest & Healing", "Light Play", "Full Recovery").