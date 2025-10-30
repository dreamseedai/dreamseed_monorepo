# Admin Front (Next.js) — Question Bank Management

A minimal admin UI for teachers/admins to manage questions (CRUD + search) with Tailwind CSS.

## Features
- Role-based access (demo via cookie): only `teacher` or `admin` can access
- List & search (keyword, topic, difficulty, status)
- Create/Edit/Delete questions
- Tailwind-styled forms and tables
- Mock API (in-memory) to be replaced with real backend endpoints later

## Run

```bash
cd admin_front
pnpm install # or npm install / yarn
pnpm dev     # http://localhost:3030
```

Then open `/login` to set your role cookie to `teacher` or `admin`.

## Replace mock API
- See `lib/questions.ts`. Wire calls to your real backend (FastAPI) when endpoints are ready.
- Types: `Question`, `QuestionInput`, `QuestionFilter`.

## RBAC
- `middleware.ts` checks `role` cookie; redirects to `/login` if missing/invalid.
- In production, replace with your real auth/JWT and server-side verification.
