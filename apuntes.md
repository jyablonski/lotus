# Apuntes

## Go


### SQLc

``` sh
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

``` proto
message User {
  int32 id = 1;
  string name = 2;
}

```

You then compile that proto file into language-specific stubs to handle all of the boilerplate code. They handle all the low-level networking, serialization, and deserialization for you. You can use `protoc` for this, but `buf` seems to be a better alternative

``` sh
protoc --go_out=./backend --go-grpc_out=./backend ./backend/internal/user.proto

grpcurl -plaintext -proto ./backend/proto/user/user.proto \
  -d '{"email": "test@gmail.com", "password": "password"}' \
  localhost:50052 internal.UserService/CreateUser

grpcurl -plaintext -proto ./backend/proto/journal/journal.proto \
  -d '{"user_id": "AAAA", "journal_text": "hello world", "user_mood": 4}' \
  localhost:50052 internal.JournalService/CreateJournal

curl -X POST http://localhost:8080/v1/users \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user@email.com",
           "password": "This123"
         }'

curl -X POST http://localhost:8080/v1/journals \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "550e8400-e29b-41d4-a716-446655440000",
           "journal_text": "This is a test journal entry.",
           "user_mood": "8"
         }'

curl -X GET "http://localhost:8080/v1/journals?user_id=user-uuid-1234"

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

``` sh
buf dep update

buf generate
```

##