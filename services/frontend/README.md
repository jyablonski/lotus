# Frontend

This directory contains the frontend code for the Lotus application, built with Next.js 14, React, and TypeScript. It provides a secure, paginated journal interface with calendar views and mood tracking.

## How It Works

**Architecture**: Next.js App Router with API proxy pattern
- **Client components** handle user interactions (forms, pagination, calendar)
- **Server components** render static content and initial page loads  
- **API routes** (`/api/*`) proxy requests to the Go backend, handling authentication server-side
- **Authentication** via Next Auth v5 with GitHub OAuth

**Security**: Frontend never directly calls the Go backend
```
Browser → /api/journals → Next.js Auth → Go Backend (hidden)
```

**Data Flow**: 
1. User interactions trigger client-side API calls to `/api/*`
2. Next.js validates session and forwards to Go backend  
3. Responses flow back through the proxy to update UI state

## Directory Structure

```
app/
├── api/                    # Next.js API routes (proxy to Go backend)
├── journal/               # Journal pages (/journal, /journal/create)
├── calendar/              # Calendar view page
└── globals.css           # Global styles

components/
├── ui/                    # Reusable UI components (buttons, cards, spinners)
├── journal/              # Journal-specific components (forms, lists, entries)
└── calendar/             # Calendar-specific components (grid, header)

hooks/
├── useJournalData.ts     # Data fetching with pagination
├── useCreateJournal.ts   # Form state management
└── useCalendarData.ts    # Calendar state and date logic

lib/
├── api/                  # API client functions (now proxy-aware)
└── utils/               # Helper functions (mood mapping, date formatting)
```

## Client vs Server Components

**Server Components** (default, no `'use client'`):
- Static content rendering
- Journal stats/insights (pre-calculated data)
- Navigation headers
- SEO-optimized pages
- Initial data fetching

**Client Components** (`'use client'` required):
- Journal entry creation forms (useState, event handlers)
- Paginated journal lists (interactive pagination controls)
- Calendar interface (date selection, month navigation)
- Search and filtering (real-time input handling)
- Modals and overlays
- Any component requiring browser APIs or interactivity

**Rule**: Use server components for display, client components for interaction.