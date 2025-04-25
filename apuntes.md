# Apuntes

## Go

## Next.js

React Server Components are rendered on the Server, so they can interact with backend services like File Systems or Databases to handle those operations on the Server and reduce the amount that has to be done on the client.

- These are rendered only on the server side

If your component involves a user pressing buttons on the website or submitting forms, then you probably need a client component.

- Client components are pre rendered on the server side to create a static shell, and then hydrate it on the client side.
- Everything on the client components that doesnt involve backend interactivity is still rendered on the server.

Dynamic Routing is when you create routes based on dynamic information like user id or name etc.

- These directories are wrapped in `[]`

Directories wrapped in `()` are Route Groups that allow you to organize layouts for your various pages without affecting the URLs

- For example, you can have your home page and the about page both use to the same `layout.tsx` file and have the about page be accessed at `/about`, but both of these pages will be stored in the `(root)` directory route group.

You can have different error pages throughout your project, but only the nearest one will be used at a time.

Static Site Generation (SSG) vs Incremental Static Regeneration (ISR)

- SSG means we build the site as HTML files at build time to improve end user performance. but, this doesn't work all that well for sites that require a lot of dynamic user information or other data to be pulled
- ISR is an extension of this where it refreshes the static page content after the site has been deployed
  - You can tell next.js to either refresh an entire page, or only refresh certain components on a set interval like every 1 hour

Static Site Rendering (SSR)

Partial Page Rendering (PPR) - Nextjs builds a static shell and dynamically streams in content where needed
