# Frontend

Next.js 15 frontend for the Lotus journal application, built with React 19, TypeScript, and Tailwind CSS 4. Provides a dark-themed journal interface with calendar views, mood tracking (1-10 scale), and analytics.

## How It Works

Architecture: Next.js App Router, server-first

- Server Components (default) fetch data directly from the Go backend via `lib/server/`
- Server Actions (`actions/`) handle mutations (creating journal entries)
- Client Components (`"use client"`) handle interactivity (forms, calendar navigation, pagination)
- Authentication via NextAuth v5 with GitHub OAuth, enforced by middleware

Data Flow:

```
Server Components -> lib/server/* -> Go Backend Gateway (:8080)
Client Components -> Server Actions (actions/*) -> Go Backend Gateway (:8080)
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

__tests__/                   # Jest unit + integration tests (377 tests)
├── server/                  # Server-side data fetching (mocked fetch)
├── actions/                 # Server action tests (mocked auth + fetch)
├── auth/                    # NextAuth callback tests
├── utils/                   # Unit tests for all utility modules
├── hooks/                   # Hook tests
├── types/                   # Type/transform tests
├── components/              # Component tests (RTL)
│   ├── journal/             # Journal components (form, editor, filters, etc.)
│   ├── calendar/            # Calendar components
│   ├── profile/             # Profile components
│   ├── nav/                 # Navbar, NavLink, UserAvatar
│   ├── auth/                # LogoutButton
│   └── ui/                  # StatCard
└── app/                     # Page tests

e2e/                         # Playwright end-to-end tests (17 tests)
├── helpers/
│   └── auth.ts              # Session cookie injection helper
├── landing.spec.ts          # Unauthenticated landing page
└── authenticated.spec.ts    # Dashboard, navigation, journal create, profile
```

## Styling

The app uses a dark theme exclusively with a hybrid CSS approach:

- Design-system classes in `globals.css` — buttons (`.btn-primary`, `.btn-outline`, `.btn-danger`), cards (`.card`, `.card-hover`), inputs (`.input-primary`, `.textarea-primary`, `.select-primary`), text (`.text-muted-dark`, `.text-primary-dark`), layout (`.page-container`, `.content-container`), badges, skeletons, and more
- One-off layout/spacing stays as inline Tailwind classes

Key theme tokens: `dark-*` (slate scale), `lotus-*` (purple), `rose-*` (accent). No light-theme colors (`bg-white`, `text-gray-700`, `bg-blue-600`, etc.) should appear in components.

## Testing

The frontend has three layers of tests:

### Unit & Integration Tests (Jest + React Testing Library)

300+ tests covering server-side data fetching, server actions, auth callbacks, utility functions, hooks, and React components.

```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:ci       # CI mode
```

| Layer          | Directory               | What it covers                                           |
| -------------- | ----------------------- | -------------------------------------------------------- | --- |
| Server-side    | `__tests__/server/`     | `lib/server/*` functions with mocked `fetch`             |
| Server actions | `__tests__/actions/`    | `createJournal` with mocked `auth()` and `fetch`         |
| Auth           | `__tests__/auth/`       | NextAuth `signIn`, `jwt`, `session` callbacks            |
| Components     | `__tests__/components/` | All journal, calendar, profile, nav, and auth components | 1   |
| Utilities      | `__tests__/utils/`      | Pure functions (mood mapping, filters, calendar, etc.)   |
| Hooks          | `__tests__/hooks/`      | `useCreateJournal`                                       |

These tests run automatically on every PR that touches `services/frontend/` via the Frontend CI / CD Pipeline workflow.

### End-to-End Tests (Playwright)

Playwright tests run against the full stack (frontend + backend + PostgreSQL) in Docker containers. Tests cover the landing page, authenticated dashboard, navigation, journal creation form, and profile page.

Authenticated tests bypass GitHub OAuth by injecting a valid NextAuth JWT session cookie using the `e2e/helpers/auth.ts` helper.

```bash
# Run locally — start the e2e stack first, then run tests
make e2e-up           # Build and start postgres, backend, frontend containers
npm run test:e2e      # Run Playwright tests against localhost:3000
npm run test:e2e:ui   # Interactive Playwright UI mode
make e2e-down         # Tear down containers and volumes
```

The `AUTH_SECRET` env var must be set to the same value the frontend container uses. The default in `docker-compose-e2e.yaml` is `e2e-test-secret-at-least-32-characters-long`.

### Triggering E2E Tests in CI

E2E tests do not run on every PR. To trigger them, add the `e2e` label to your pull request. This runs the Frontend E2E Tests workflow (`.github/workflows/e2e.yaml`), which:

1. Starts the full stack via `docker compose -f docker/docker-compose-e2e.yaml`
2. Waits for the frontend to be healthy
3. Installs Playwright and runs all e2e tests

## Development

```bash
npm run dev           # Start dev server (port 3000)
npm run build         # Production build
npm run lint          # ESLint
```

Or via the monorepo root: `make up` starts all services including the frontend with hot-reload via Tilt.
