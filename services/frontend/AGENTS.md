# Frontend Service - Agent Guide

Next.js 15 frontend application with React 19, TypeScript, and Tailwind CSS for the journal application UI.

## Technology Stack

- **Framework**: Next.js 15.3.1
- **React**: React 19
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS 4.1.4
- **UI Components**: shadcn/ui (via components.json)
- **Authentication**: NextAuth.js 5.0 (beta)
- **Testing**: Jest with React Testing Library
- **Package Manager**: npm 11.2.0

## Architecture Patterns

### App Router (Next.js 15)

Next.js 15 uses the **App Router** architecture:

- Routes are defined by folder structure in `app/`
- Server Components by default
- Client Components marked with `"use client"`
- Server Actions for mutations
- Route handlers for API endpoints

### Component Organization

- **Server Components** - Default, run on server
- **Client Components** - Marked with `"use client"`, run in browser
- **Server Actions** - Functions that run on server, called from client

### Data Fetching

- **Server Components** - Direct data fetching (no hooks)
- **Client Components** - Use React hooks (`useState`, `useEffect`)
- **Server Actions** - Mutations via `actions/` directory

## Code Organization

```
app/                          # Next.js App Router
├── (auth)/                   # Auth route group
│   └── signin/
├── (dashboard)/              # Dashboard route group
│   ├── dashboard/
│   ├── journals/
│   └── analytics/
├── api/                      # API route handlers
│   └── auth/
├── layout.tsx                # Root layout
├── page.tsx                  # Home page
└── globals.css               # Global styles

components/                   # React components
├── ui/                       # shadcn/ui components
│   ├── Card.tsx
│   └── ...
└── ...                       # Custom components

actions/                      # Server Actions
├── index.ts
└── journals.ts

lib/                          # Utility libraries
├── api/                      # API client
├── server/                   # Server-side utilities
│   ├── analytics.ts
│   ├── journals.ts
│   └── profile.ts
└── utils/                    # Client utilities
    ├── calendar.ts
    ├── dashboard.ts
    └── ...

hooks/                        # Custom React hooks
├── useJournal.ts
└── ...

types/                        # TypeScript types
├── analytics.ts
└── journal.ts

utils/                        # Utility functions
└── moodMapping.ts
```

## Key Patterns

### Server Component

```tsx
// app/dashboard/page.tsx (Server Component)
import { getJournals } from "@/lib/server/journals";

export default async function DashboardPage() {
  const journals = await getJournals();

  return <div>{/* Render journals */}</div>;
}
```

### Client Component

```tsx
// components/JournalList.tsx
"use client";

import { useState } from "react";

export function JournalList() {
  const [journals, setJournals] = useState([]);

  return <div>{/* Interactive UI */}</div>;
}
```

### Server Action

```tsx
// actions/journals.ts
"use server";

export async function createJournal(data: FormData) {
  // Server-side logic
  const response = await fetch("...");
  return response.json();
}

// Usage in component
import { createJournal } from "@/actions/journals";

export function JournalForm() {
  async function handleSubmit(formData: FormData) {
    await createJournal(formData);
  }

  return <form action={handleSubmit}>...</form>;
}
```

### API Route Handler

```tsx
// app/api/journals/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  const data = await fetchData();
  return NextResponse.json(data);
}
```

## Testing

### Test Structure

- Tests are in `__tests__/` directory
- Test files: `*.test.tsx` or `*.test.ts`
- Use Jest with React Testing Library

### Running Tests

```bash
# Run tests
npm test

# Watch mode
npm run test:watch

# CI mode
npm run test:ci
```

### Test Patterns

```tsx
import { render, screen } from "@testing-library/react";
import { JournalCard } from "@/components/JournalCard";

describe("JournalCard", () => {
  it("renders journal title", () => {
    render(<JournalCard journal={mockJournal} />);
    expect(screen.getByText("Journal Title")).toBeInTheDocument();
  });
});
```

## Configuration

### Environment Variables

- `NEXTAUTH_URL` - Base URL for NextAuth (default: `http://localhost:3000`)
- `BACKEND_URL` - Backend API URL (default: `http://backend:8080`)
- `AUTH_SECRET` - Secret for NextAuth (required)
- `AUTH_GITHUB_ID` - GitHub OAuth client ID
- `AUTH_GITHUB_SECRET` - GitHub OAuth client secret
- `AUTH_TRUST_HOST` - Trust host header (default: `true`)

### Next.js Configuration

- `next.config.ts` - Next.js configuration
- TypeScript config: `tsconfig.json`
- ESLint config: `eslint.config.mjs`
- Tailwind config: `tailwind.config.ts` (or via CSS)

## Key Files to Understand

Before making changes:

1. **`app/layout.tsx`** - Root layout and providers
2. **`app/page.tsx`** - Home page
3. **`middleware.ts`** - Next.js middleware (auth, etc.)
4. **`components/ui/`** - shadcn/ui components
5. **`lib/server/`** - Server-side data fetching
6. **`actions/`** - Server Actions for mutations
7. **`types/`** - TypeScript type definitions

## Common Tasks

### Adding a New Page

1. Create route folder in `app/`
2. Add `page.tsx` file (Server Component)
3. Add layout if needed: `layout.tsx`
4. Add types in `types/` if needed
5. Add server-side data fetching in `lib/server/`

### Creating a Component

1. Create component file in `components/`
2. Determine if Server or Client Component
3. Add `"use client"` directive if Client Component
4. Use TypeScript for type safety
5. Add to appropriate route/page

### Adding Server-Side Data Fetching

1. Create function in `lib/server/`
2. Use `fetch` with backend URL
3. Handle errors appropriately
4. Return typed data
5. Call from Server Component

### Creating a Server Action

1. Create function in `actions/`
2. Add `"use server"` directive
3. Accept FormData or typed parameters
4. Call backend API
5. Return result or redirect
6. Use in form `action` prop

### Adding API Route

1. Create route file: `app/api/{route}/route.ts`
2. Export HTTP methods: `GET`, `POST`, etc.
3. Use `NextResponse` for responses
4. Handle errors with try/catch

### Styling Components

1. Use Tailwind CSS classes
2. Use shadcn/ui components for common UI patterns
3. Create custom components in `components/ui/` if needed
4. Follow design system patterns

## Code Style

### TypeScript

- Use strict TypeScript
- Define types in `types/` directory
- Use type inference where appropriate
- Avoid `any` type

### React Patterns

- Prefer Server Components when possible
- Use Client Components only for interactivity
- Use Server Actions for mutations
- Keep components focused and single-purpose

### Styling

- Use Tailwind CSS utility classes
- Follow mobile-first responsive design
- Use shadcn/ui components for consistency
- Create reusable component variants

## Authentication

### NextAuth.js

- Authentication handled by NextAuth.js
- GitHub OAuth provider configured
- Session management via cookies
- Protected routes via middleware

### Protected Routes

- Use middleware to protect routes
- Check authentication in Server Components
- Redirect to sign-in if not authenticated

## API Integration

### Backend Communication

- Backend API: `BACKEND_URL` environment variable
- Use `fetch` for API calls
- Server-side calls from Server Components/Actions
- Client-side calls from Client Components (via hooks)

### Error Handling

- Handle API errors gracefully
- Show user-friendly error messages
- Log errors for debugging
- Use try/catch for async operations

## State Management

### Server State

- Fetch data in Server Components
- Pass data as props to Client Components
- Revalidate on demand or via time-based revalidation

### Client State

- Use React hooks (`useState`, `useEffect`)
- Use custom hooks for reusable logic
- Consider React Query for complex client state (if needed)

## Performance

### Optimization

- Use Server Components for better performance
- Implement code splitting via dynamic imports
- Optimize images with Next.js Image component
- Use React Server Components for data fetching

### Caching

- Next.js automatically caches Server Component data
- Use `revalidate` for time-based revalidation
- Use `cache` function for request memoization

## Pre-commit Hooks

- Prettier formatting (via pre-commit)
- ESLint linting (Next.js config)
- Type checking via TypeScript

## Deployment

- Uses `Dockerfile` for containerization
- Port: 3000
- Environment variables required for production
- Build command: `npm run build`
- Start command: `npm start`

## Best Practices

1. **Server Components First**: Use Server Components by default
2. **Type Safety**: Use TypeScript for all code
3. **Component Composition**: Build complex UIs from simple components
4. **Error Handling**: Handle errors gracefully
5. **Accessibility**: Follow WCAG guidelines
6. **Performance**: Optimize images and code splitting
7. **Testing**: Write tests for critical components
8. **Documentation**: Document complex logic and components
