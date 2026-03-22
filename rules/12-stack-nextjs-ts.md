# rules/12-stack-nextjs-ts.md — NEXT.JS / TYPESCRIPT

## SUMMARY (READ FIRST)
- TypeScript strict mode, avoid `any`.
- Next.js App Router conventions (Server/Client Components, route handlers).
- Tailwind CSS utility-first styling.
- Prisma / Zod integration patterns.

## RULES
### R1) TypeScript
- Enable strict mode. Avoid `any` — use `unknown` + type guards.
- Prefer `interface` for object shapes, `type` for unions/intersections.
- Use `satisfies` operator for type-safe object literals.
- Use `as const` for literal type inference.

### R2) Next.js App Router
- Default to Server Components. Add `"use client"` only when needed (hooks, event handlers, browser APIs).
- Use `route.ts` for API routes (GET, POST, etc.).
- Dynamic data: add `export const dynamic = "force-dynamic"` for pages with DB queries at build time.
- Loading/Error UI: use `loading.tsx`, `error.tsx` conventions.

### R3) Tailwind CSS
- Utility-first: prefer Tailwind classes over custom CSS.
- Consistent spacing: use Tailwind's spacing scale (p-4, m-2, gap-3).
- Responsive: mobile-first with `sm:`, `md:`, `lg:` breakpoints.
- Dark mode: use `dark:` variant when applicable.

### R4) Prisma
- Schema: use `url = env("DATABASE_URL")` in datasource block.
- Singleton: reuse PrismaClient instance (prevent connection pool exhaustion in dev).
- Server-only: never import Prisma in client components.
- JSON fields: use `z.record(z.string(), z.unknown())` with Zod, cast with `as object` for Prisma's `InputJsonValue`.

### R5) Zod Validation
- Validate at system boundaries (API routes, form submissions).
- Zod 4: `z.record()` requires 2 args: `z.record(z.string(), z.unknown())`.
- Use `z.infer<typeof schema>` for type derivation.

### R6) State Management
- Server state: TanStack React Query (useQuery, useMutation).
- Client state: React hooks (useState, useReducer) — keep it simple.
- Form state: React Hook Form + Zod resolver when forms are complex.

### R7) Error Handling
- API routes: return proper HTTP status codes with typed error responses.
- Client: use Error Boundaries and toast notifications.
- Never expose stack traces or internal errors to the client.

### R8) Testing
- Unit: Vitest or Jest with React Testing Library.
- E2E: Playwright.
- Test naming: `describe` + `it` blocks with clear descriptions.

## EXAMPLES
- BAD: `const data: any = await fetch(...)`
- GOOD: `const data: UserResponse = await fetch(...).then(r => r.json())`
- BAD: `export default function Page() { const users = prisma.user.findMany() }` (build-time error)
- GOOD: Add `export const dynamic = "force-dynamic"` above the component
