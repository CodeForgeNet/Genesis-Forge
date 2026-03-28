---
description: AI-powered design intelligence. 50+ styles, 97 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types across 9 stacks.
---

# /ui-ux-pro-max

## STEP 1: Analyze Request (silent)
Extract: product type, style keywords, industry, stack (default: `html-tailwind`)

## STEP 2: Generate Design System (ALWAYS run first)
```bash
python3 agent/.shared/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```
Add `--persist` to save to `design-system/MASTER.md` for cross-session use.
Add `--page "dashboard"` to create page-specific override at `design-system/pages/dashboard.md`.

**Hierarchy:** `design-system/pages/<page>.md` overrides `design-system/MASTER.md`.

## STEP 3: Supplement (as needed)
```bash
python3 agent/.shared/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain>
```
| Need | Domain |
|------|--------|
| Style options | `style` |
| Charts | `chart` |
| UX best practices | `ux` |
| Fonts | `typography` |
| Landing structure | `landing` |

## STEP 4: Stack Guidelines
```bash
python3 agent/.shared/ui-ux-pro-max/scripts/search.py "<keyword>" --stack html-tailwind
```
Stacks: `html-tailwind` `react` `nextjs` `vue` `svelte` `swiftui` `react-native` `flutter` `shadcn` `jetpack-compose`

---

## Common Rules (Non-Negotiable)

| Area | Do | Don't |
|------|----|-------|
| Icons | SVG (Heroicons/Lucide) | Emojis as icons |
| Cursor | `cursor-pointer` on all clickables | Default cursor on interactive elements |
| Transitions | `transition-colors duration-200` | Instant or >500ms changes |
| Light mode glass | `bg-white/80`+ | `bg-white/10` (invisible) |
| Text contrast | `#0F172A` slate-900 | `#94A3B8` slate-400 for body |
| Navbar | `top-4 left-4 right-4` floating | Stuck to `top-0` |

---

## Pre-Delivery Checklist
- [ ] No emoji icons — SVG only
- [ ] All clickables have `cursor-pointer`
- [ ] Light mode text contrast ≥ 4.5:1
- [ ] Glass elements visible in light mode
- [ ] Responsive at 375 / 768 / 1024 / 1440px
- [ ] No horizontal scroll on mobile
- [ ] Focus states visible
- [ ] `prefers-reduced-motion` respected
- [ ] All images have alt text
