# Frontend

Next.js 15 frontend for the Lotus journal application, built with React 19, TypeScript, and Tailwind CSS 4. Provides a dark-themed journal interface with calendar views, mood tracking (8-point scale), and analytics.

## How It Works

**Architecture**: Next.js App Router, server-first

- **Server Components** (default) fetch data directly from the Go backend via `lib/server/`
- **Server Actions** (`actions/`) handle mutations (creating journal entries)
- **Client Components** (`"use client"`) handle interactivity (forms, calendar navigation, pagination)
- **Authentication** via NextAuth v5 with GitHub OAuth, enforced by middleware

**Data Flow**:

```
Server Components → lib/server/* → Go Backend Gateway (:8080)
Client Components → Server Actions (actions/*) → Go Backend Gateway (:8080)
```

Server components call the backend directly at build/request time. There is no client-side API proxy layer.

## Directory Structure

```
app/
├── (root)/                  # Authenticated route group
│   ├── page.tsx             # Home / dashboard
│   ├── admin/               # Admin page (email-gated)
│   ├── journal/
│   │   ├── home/            # Journal list with filters + pagination
│   │   ├── create/          # New journal entry form
│   │   └── calendar/        # Calendar view
│   └── profile/             # User profile + insights
├── api/auth/[...nextauth]/  # NextAuth route handler
├── globals.css              # Design system (utility classes, theme)
└── layout.tsx               # Root layout + providers

components/
├── ui/                      # Shared UI (Card, CardHeader, StatCard, ErrorFallback, etc.)
├── journal/                 # Journal components (form, editor, filters, pagination, cards)
├── calendar/                # Calendar grid + selected date entries
├── dashboard/               # LoggedInDashboard
├── landing/                 # LandingPage (unauthenticated)
├── profile/                 # ProfileActions, ProfileInsights, ProfileHeader, ProfileStats
├── auth/                    # LogoutButton
├── Navbar.tsx               # Navigation bar
└── UserAvatar.tsx           # User avatar component

actions/
├── index.ts                 # Server action utilities
└── journals.ts              # createJournal server action

lib/
├── server/                  # Server-side data fetching (journals, analytics, profile)
└── utils/                   # Pure utility functions (mood mapping, filters, calendar, dashboard, profile stats)

hooks/
└── useCreateJournal.ts      # Client-side form state for journal creation

types/
├── journal.ts               # JournalEntry, BackendJournal, CalendarDay
└── analytics.ts             # UserJournalSummary

__tests__/                   # Jest + React Testing Library (134 tests)
├── utils/                   # Unit tests for all utility modules
├── hooks/                   # Hook tests
├── types/                   # Type/transform tests
├── ui/                      # UI component tests
├── components/              # Component tests
└── app/                     # Page tests
```

## Styling

The app uses a **dark theme exclusively** with a hybrid CSS approach:

- **Design-system classes** in `globals.css` — buttons (`.btn-primary`, `.btn-outline`, `.btn-danger`), cards (`.card`, `.card-hover`), inputs (`.input-primary`, `.textarea-primary`, `.select-primary`), text (`.text-muted-dark`, `.text-primary-dark`), layout (`.page-container`, `.content-container`), badges, skeletons, and more
- **One-off layout/spacing** stays as inline Tailwind classes

Key theme tokens: `dark-*` (slate scale), `lotus-*` (purple), `rose-*` (accent). No light-theme colors (`bg-white`, `text-gray-700`, `bg-blue-600`, etc.) should appear in components.

## Testing

```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:ci       # CI mode with coverage
```

130+ tests covering utility functions, hooks, types, UI components, and pages.

## Development

```bash
npm run dev           # Start dev server (port 3000)
npm run build         # Production build
npm run lint          # ESLint
```

Or via the monorepo root: `make up` starts all services including the frontend with hot-reload via Tilt.

## Environment Variables

| Variable             | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `BACKEND_URL`        | Go backend gateway URL (default: `http://backend:8080`) |
| `AUTH_SECRET`        | NextAuth secret (required)                              |
| `AUTH_GITHUB_ID`     | GitHub OAuth client ID                                  |
| `AUTH_GITHUB_SECRET` | GitHub OAuth client secret                              |
| `AUTH_TRUST_HOST`    | Trust host header (default: `true`)                     |
| `ADMIN_EMAILS`       | Comma-separated admin email addresses                   |
