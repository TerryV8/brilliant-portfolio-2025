# Notion Clone (Next.js + Tailwind v4 + shadcn)

A Notion-style app scaffold built with:

- Next.js App Router (`app/`)
- Tailwind CSS v4 (no tailwind.config required by default)
- shadcn UI (New York theme, neutral base color)

This repo is the frontend foundation. Backend (Convex) and auth will be added later.

## Tech Stack

- Next.js 15 (React 19)
- Tailwind CSS v4 via `@tailwindcss/postcss`
- shadcn (components.json configured, utilities ready)
- Fonts: Geist via `next/font`

## Getting Started

Install dependencies and run the dev server:

```bash
npm install
npm run dev
# open http://localhost:3000
```

Edit `app/page.tsx` and `app/layout.tsx`. Global styles live in `app/globals.css`.

## shadcn

The project is initialized for shadcn. Add components as needed, for example:

```bash
npx shadcn@latest add button
npx shadcn@latest add input
```

Utilities:

- `lib/utils.ts` exports `cn()` combining `clsx` and `tailwind-merge`.

Configuration:

- `components.json` points to `app/globals.css` and uses `@/*` aliases.

## Tailwind CSS v4

- Imported via `@import "tailwindcss";` in `app/globals.css`.
- PostCSS plugin is configured in `postcss.config.mjs`.
- A `tailwind.config` file is optional. Add one only if you need customizations beyond `@theme`/CSS variables in `globals.css`.

## Scripts

- `npm run dev` – Start dev server
- `npm run build` – Production build
- `npm run start` – Start production server
- `npm run lint` – Lint using ESLint

## Project Structure

```
notion-clone/
├─ app/
│  ├─ layout.tsx         # App shell, imports globals.css
│  ├─ page.tsx           # Home page
│  └─ globals.css        # Tailwind v4, theme tokens, CSS variables
├─ lib/
│  └─ utils.ts           # cn() helper
├─ components.json       # shadcn settings
├─ postcss.config.mjs    # Tailwind v4 PostCSS plugin
├─ tsconfig.json         # @/* path alias
├─ next.config.ts
└─ package.json
```

## Environment Variables (planned)

- Convex and Auth will be added later. This section will be updated with required env keys.

## Roadmap

- Add shadcn components (button, input, dialog, dropdown, sheet, tooltip)
- Integrate Convex (documents, pages, real-time)
- Authentication (provider TBD)
- Rich text editor
- Collaborative cursors/presence

## Deployment

Deployed best on Vercel. After configuring environment variables (once backend/auth are added):

```bash
npm run build
npm run start
```

## License

MIT
