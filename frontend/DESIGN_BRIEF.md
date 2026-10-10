# DESIGN_BRIEF.md — AgentBreak Visual Direction & Design Tokens (Flat Editorial Edition)

> **VISUAL THEME: CLEAN EDITORIAL SAAS**
> High-contrast flat editorial canvas, pure white and subtle beige card containers, crisp 1px borders,
> zero shadows, and muted organic color accents.

---

## 1. Design Philosophy
- **Background Canvas**: `#F9F8F6` (Pearl Cream)
- **Card & Surface**: `#FFFFFF` (Pure White) with `border border-beige` and `rounded-xl`
- **Soft Elevation**: Flat UI (no shadows)
- **Typography**:
  - Primary text: `#1C1C1A` (Deep Charcoal)
  - Headings (h1, h2, h3): `Playfair Display, serif`
  - Body & Data (p, span, div): `Inter, sans-serif`
  - Monospace (Keys, Canaries, Payloads, Steps): `JetBrains Mono, monospace`
- **Status Pills & Semantic Accents**:
  - Breach / Exfiltration: `bg-white text-charcoal border-beige`
  - Resisted / Policy Blocked: `bg-white text-charcoal border-beige`
  - Active Tab / Brand: `bg-white text-charcoal border-beige shadow-sm`
  - Demo Status: `bg-[#E6F4EA] text-[#137333]`

---

## 2. Updated Light Viewports
1. **Header Navigation (`Navbar.tsx`)**:
   - `bg-pearl/90 backdrop-blur-md border-b border-beige/40`
   - Active tab pills: `bg-white text-charcoal border border-beige shadow-sm`
   - Logo: Minimalist circular black and white brand mark.
2. **Executive Dashboard (`Dashboard.tsx`)**:
   - Crisp KPI metric cards with muted organic data viz colors.
   - Recharts bar chart styled with charcoal (`#1C1C1A`), muted red (`#9D3B31`), and muted green (`#2E6A4F`).
   - Clean flat table with pure white headers.
3. **Campaign Runner (`CampaignRunner.tsx`)**:
   - React Flow attack graph on clean `#F9F8F6` background.
   - Pure-white node tiles with colored accent borders matching the muted palette.
   - Real-time Server-Sent Events stream feed with light flat beige cards.
4. **Findings & Forensic Inspector (`Findings.tsx`)**:
   - Filterable attack list with clean category pills.
   - Objective oracle verification callouts in light beige flat boxes.
   - Trace steps in muted beige boxes with minimalist border role badges.
5. **Defenses Matrix (`Defenses.tsx`)**:
   - 5 pluggable defense toggles in clean white flat tiles.
   - Security vs. Utility tradeoff scatter chart using charcoal `#1C1C1A` data points.
   - Comparative Attacks × Defenses matrix table.
6. **Executive Report (`Report.tsx`)**:
   - Standalone printable HTML report preview and JSON export buttons.
