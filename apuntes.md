# Apuntes

## Go

### SQLc

```sh
sqlc generate -f backend/internal/sqlc.yaml
```

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

### Implementation

## Proto

Protocol Buffers (protobuf) are a language-agnostic way to serialize structured data. They also provide auto-generated code for reading and writing data, so you can focus on your implementation of what the service does like write to Postgres etc.

In gRPC, `.proto` files define the structure of your data and services—they act as a contract between the client and server. You define request and response messages, including the fields and their types.

```proto
message User {
  int32 id = 1;
  string name = 2;
}

```

You then compile that proto file into language-specific stubs to handle all of the boilerplate code. They handle all the low-level networking, serialization, and deserialization for you. You can use `protoc` for this, but `buf` seems to be a better alternative

```sh
protoc --go_out=./backend --go-grpc_out=./backend ./backend/internal/user.proto

grpcurl -plaintext -proto ./backend/proto/user/user.proto \
  -d '{"email": "test@gmail.com", "password": "password"}' \
  localhost:50052 internal.UserService/CreateUser

grpcurl -plaintext -proto ./backend/proto/journal/journal.proto \
  -d '{"user_id": "AAAA", "journal_text": "hello world", "user_mood": 4}' \
  localhost:50052 internal.JournalService/CreateJournal

protoc -I. \
  -I$(go list -f '{{ .Dir }}' -m github.com/grpc-ecosystem/grpc-gateway/v2) \
  -I$(go list -f '{{ .Dir }}' -m github.com/googleapis/googleapis) \
  --go_out=. \
  --go-grpc_out=. \
  --grpc-gateway_out=. \
  internal/user.proto

protoc -I. \
  -I$(go list -f '{{ .Dir }}' -m github.com/grpc-ecosystem/grpc-gateway/v2) \
  -I$(go list -f '{{ .Dir }}' -m github.com/googleapis/googleapis) \
  --go_out=internal/user_pb \
  --go-grpc_out=internal/user_pb \
  --grpc-gateway_out=internal/user_pb \
  internal/user.proto
```

With `buf`, you setup `buf.yaml` and `buf.gen.yaml` files

- `buf.gen.yaml` defines defines how to generate code (e.g., Go, Python, gRPC stubs) from your .proto files using plugins.
- `buf.yaml` defines config options like linting, how protobuf files are organized, and other dependencies etc
- A `buf.lock` file locks those dependencies and versions similar to a `package-lock.json` or `go.sum` file

```sh
buf dep update

buf generate
```

## TypeScript

```
import { Login } from "@/components/auth/login-button";
import { Logout } from "@/components/auth/logout-button";
```

- Importing a named export, not the default export from that file

---

There are **two types of exports** in a module:

| Type               | Syntax to Export                                                    | Syntax to Import                        | Example                                   |
| ------------------ | ------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------- |
| **Default Export** | `export default ComponentName;`                                     | `import ComponentName from "path";`     | `import Navbar from "./Navbar";`          |
| **Named Export**   | `export { ComponentName };` or `export function ComponentName() {}` | `import { ComponentName } from "path";` | `import { Login } from "./login-button";` |

---

In JSX, all components (and HTML tags) must be properly closed.

- That's why you write `<Logout />` and not `<Logout>` alone.

## Ongoing bugs

1. frontend bug when making journal entries - i made an entry at monday oct 27 5:02 pm pt nd it shows up as it was created on tuesday oct 28, and tells me to create my first journal entry on the 27th

## uv Version alignment

True Single Source of Truth Approach

1. Create .tool-versions or UV_VERSION file at root:
   0.9.18
2. Dockerfiles — use ARG only (no default):
   ARG UV_VERSIONRUN pip install uv==${UV_VERSION} && \ uv sync --frozen --no-dev --no-install-project
3. docker-compose — read from file and pass as build arg:
   services: analyzer: build: context: ${PWD}/services/analyzer args: UV_VERSION: ${UV_VERSION}
   Then create a .env file (or source script) that reads from .tool-versions:

- `.env or a scriptUV_VERSION=$(cat .tool-versions | grep -E '^[0-9]' | head -1)export UV_VERSION`

4. CI workflows — read from file in a step:

- name: Set UV version run: echo "UV_VERSION=$(cat .tool-versions | grep -E '^[0-9]' | head -1)" >> $GITHUB_ENV- name: Install uv uses: astral-sh/setup-uv@v6 with: version: ${{ env.UV_VERSION }}

Or even better: Use a Script/Helper

Create a script that reads the version and exports it, then source it everywhere:

```sh
scripts/get-uv-version.sh:
#!/bin/bash
# Reads UV version from .tool-versions file
cat .tool-versions | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' | head -1
```

Then:

- docker-compose: Use a script to set the env var before running
- CI: Use the script in a step
- Makefile: Use the script to set the variable
