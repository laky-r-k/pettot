---
name: Clinical Recovery Telemetry
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
  on-surface-variant: '#c5c6cd'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#8f9097'
  outline-variant: '#45474c'
  surface-tint: '#bcc7de'
  primary: '#bcc7de'
  on-primary: '#263143'
  primary-container: '#1e293b'
  on-primary-container: '#8590a6'
  inverse-primary: '#545f73'
  secondary: '#c1c7cf'
  on-secondary: '#2b3137'
  secondary-container: '#41474e'
  on-secondary-container: '#afb6bd'
  tertiary: '#b7c8e1'
  on-tertiary: '#213145'
  tertiary-container: '#1a2a3e'
  on-tertiary-container: '#8191a9'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e3fb'
  primary-fixed-dim: '#bcc7de'
  on-primary-fixed: '#111c2d'
  on-primary-fixed-variant: '#3c475a'
  secondary-fixed: '#dde3eb'
  secondary-fixed-dim: '#c1c7cf'
  on-secondary-fixed: '#161c22'
  on-secondary-fixed-variant: '#41474e'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.06em
  telemetry-metric:
    fontFamily: JetBrains Mono
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
spacing:
  gutter: 1rem
  gutter-mobile: 0.5rem
  margin: 1.5rem
  margin-mobile: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system serves veterinary surgical teams, intensive care units, and post-operative monitoring specialists. The operational environment demands sustained visual endurance, zero ambiguity during acute medical interventions, and uncompromising data density. The interface rejects consumer pet-tech tropes—there are no playful character motifs, soft rounded cards, or celebratory animations. Instead, it adopts the posture of an architectural diagnostic instrument.

The design movement is **Technical Precision / Modern Clinical**:
- **Aesthetic Tenets**: Hairline architectural framing, structured metadata compartments, tabular alignment, and deliberate restraint. Visual hierarchy is established through spatial density, scale, and typographic weight rather than decorative fills.
- **Operational Tone**: Authoritative, calm, vigilant, and objective. Telemetry streams, analgesic schedules, and biometric deltas are presented with laboratory-grade legibility.
- **Surface Philosophy**: Deep clinical slate foundations paired with warm bone structural zones to reduce ocular fatigue under sterile operative lighting and dark ICU monitoring wards.

## Colors

The palette is engineered for clinical decision-making under low-light surgical and recovery wards. Primary focus is maintained through an ultra-low saturation neutral spectrum, reserving color almost exclusively for state semantics, telemetry signals, and triage prioritization.

### Surface Architecture
- **Base Canvas**: Deep Slate (`#0B0F17` / `#0F172A`) provides an ink-like, non-glare foundation.
- **Containers & Cells**: Layered Slate (`#1E293B`) defines distinct data tables, waveform backgrounds, and sensor logs.
- **Structural Text & High-Contrast Accents**: Warm Bone (`#F8FAFC` to `#E2E8F0`) establishes primary reading clarity without the stark ocular buzz of pure white.
- **Subordinate Framing**: Hairline Muted Borders (`#334155`) trace out structural grids, patient boundaries, and vital signal limits.

### Tri-State Telemetry Tokens
Color is strictly semantic and applied with functional restraint:
- **Critical Deviation / Alert**: Crimson (`#D9383A`). Used strictly for cardiac arrhythmia, airway compromise, severe hypothermia, or immediate pain escalation.
- **Clinical Review Required**: Amber (`#D97706`). Used for marginal trends, threshold crossings, pending IV re-doses, and observational check-ins.
- **Normal Recovery / Progressing**: Emerald (`#059669`). Confirms steady baseline metrics, normal post-anesthesia extubation, and stable vitals.
- **Auxiliary System & Telemetry Traces**: Cyan/Steel (`#0EA5E9` / `#38BDF8`) reserved exclusively for raw signal paths (e.g., plethysmograph waveforms, respiratory rate monitors).

## Typography

The typographic hierarchy balances structural command, legible narrative documentation, and hyper-precise real-time readouts.

- **Headlines (`Space Grotesk`)**: Provides an architectural, surgical edge without sacrificing human scale. Used for ward views, patient cohort titles, and surgical procedure classifications.
- **Body (`Hanken Grotesk`)**: Delivers supreme clarity in multi-line clinical logs, surgical notes, medication contraindications, and handover summaries.
- **Provenance & Telemetry Labels (`JetBrains Mono`)**: Strict tabular lining figures and fixed widths prevent optical jitter when biometric figures update continuously. Used for real-time SpO2, heart rate (BPM), core body temperature (°C/°F), infusion pump rates (mL/hr), and device timestamps. All numeric telemetry must align on the right tabular axis.

## Layout & Spacing

Layouts follow an operational control-room framework built on continuous, high-density modular units. Space serves to group critical data streams rather than create decorative air.

- **System Model**: A 12-column architectural matrix with tight gutters (`1rem` on desktop, `0.5rem` on tactical tablets/mobile) maximizing screen real estate for concurrent patient monitors.
- **Zonal Distribution**:
  - **Global Header / Ward Status Bar**: Fixed 48px vertical height displaying clinic site, ICU bed count, active alert tallies, and synchronized master time.
  - **Telemetry Multi-Feed**: Flexible 3-column or 4-column sub-grids displaying simultaneous vital strip monitors.
  - **Detail & Provenance Drawer**: Docked 360px–420px contextual rail for deep log examination and dosing logs without obscuring core monitoring.
- **Adaptation**:
  - **Mobile / Diagnostic Handheld**: Shifts from multi-patient overview into a single-patient vertical feed. Margins drop to `0.75rem`. Tabular monitors swap from continuous waveforms to immediate state sparklines and tabular status badges.

## Elevation & Depth

Visual depth is achieved through **Tonal Layering and Hairline Outlines**, strictly rejecting soft ambient shadows, floating cards, or glassy blurs that obscure high-frequency medical information.

- **Level 0 (Operating Canvas)**: `#0B0F17`. The void background on which clinical instrumentation rests.
- **Level 1 (Patient Bay / Telemetry Strip)**: `#151D2A`. Flat, solid container with a 1px border of `#334155` (or status-tinted borders when alarms activate).
- **Level 2 (Active Focus / Selected Feed)**: `#1E293B`. Distinguishes an interrogated patient tile or focused vital parameter. Outlines elevate to `#475569`.
- **Level 3 (Urgent Interventions / Modal Overlays)**: `#1E293B` backed by a 60% opacity `#000000` blackout veil. Borders are crisp 1px `#64748B`. No drop shadows; containment is strictly geometric.
- **State Highlighting**: Critical alerts override surface boundaries: an active alert shifts the cell border from neutral slate to Crimson (`#D9383A`) with an ultra-subtle, non-distracting 10% crimson surface flood.

## Shapes

The design system enforces a **Sharp (`0`)** shape language throughout the interface.

- **Geometry**: Precision right angles (0px radius) across all viewports, patient cards, telemetry containers, input fields, and action buttons. 
- **Rationale**: Filleted corners waste pixel real estate in high-density grids and introduce soft, domestic undertones contrary to high-acuity surgical operations. Orthogonal edges reinforce clinical rigidity, strict grid alignment, and accurate waveform bounding boxes.
- **Internal Accents**: Micro-chamfers (1px clipped corners) may be employed exclusively on patient status indicators and hardware connection flags to denote diagnostic device status.

## Components

### Buttons & Clinical Triggers
- **Action Paradigm**: Monospaced labels, upper-case tracking (`JetBrains Mono`, 11px), 0px corner radius, strict 32px or 36px fixed heights.
- **Primary / Commit**: Solid `#E2E8F0` surface with `#0F172A` text. Hover shifts to `#CBD5E1`.
- **Secondary / Command**: `#1E293B` surface, `#94A3B8` border (1px), `#F1F5F9` text.
- **Destructive / Alarm Silence**: Transparent fill, `#D9383A` 1px border, `#D9383A` text. On active hold/depress, fills with `#D9383A` and displays inverse `#FFFFFF` text.

### Telemetry Badges & Chips
- Compact, flat components with 1px hairline borders.
- Background uses a 12% tint of the respective token (`#D9383A` for Alert, `#D97706` for Review, `#059669` for Progressing), paired with solid matching status text in `JetBrains Mono` (10px, bold).
- Includes a leading 6px square glyph (green pulse, amber dash, crimson flashing diamond) to guarantee colorblind accessibility.

### Vital Telemetry Cards
- Structured as modular cells with fixed headers: Species & ID (e.g., `CANINE // POST-OP SPAY // BED 04`), followed by synchronized real-time values.
- Primary metric displayed in `telemetry-metric` font size, accompanied by unit of measure and delta trend arrows (`▲ +1.2% / 15m`).
- Integrated miniature sparkline canvases rendered in single-pixel vector fidelity against dark slate backdrops.

### Lists & Auditing Tables
- High-density tabular layouts with 28px row heights.
- Alternating subtle row divisions via 1px border `#1E293B`.
- All timestamps presented in ISO 8601 or 24-hour UTC/Local format (`14:22:08.102`) using tabular monospace.

### Inputs & Dosage Controls
- Dark slate `#151D2A` input boxes framed with 1px `#334155`.
- Active focus state: crisp `#E2E8F0` 1px border with zero glow or blur.
- Number steppers and infusion quantity selectors feature explicit decrement/increment step segments with high-contrast tactile feedback.

### Checkboxes & Segmented Radios
- Box dimensions: 14px × 14px sharp squares.
- Unchecked: `#151D2A` fill with 1px `#475569` border.
- Checked: `#E2E8F0` fill with a centered `#0F172A` solid core square.