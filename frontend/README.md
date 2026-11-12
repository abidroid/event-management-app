# Acme Events — frontend

React + Vite + TypeScript client for the Corporate Event Management API.

## Stack

Tailwind CSS v4, shadcn/ui (Radix), TanStack Query, React Router,
react-hook-form + zod, lucide-react icons and sonner toasts.

## Run

Start the backend first (from the repository root):

```powershell
uv run fastapi dev app/main.py
```

Then, in another terminal:

```powershell
cd frontend
copy .env.example .env   # optional: VITE_API_URL defaults to http://127.0.0.1:8000
npm install
npm run dev              # http://localhost:5173
```

The backend only accepts browser requests from the origins in its
`CORS_ORIGINS` setting (default `http://localhost:5173`).

## Checks

```powershell
npm run build   # type-check (tsc) and production build
npm run lint    # oxlint
```

## Structure

| Path | Purpose |
| --- | --- |
| `src/lib/api.ts` | Typed fetch functions for every endpoint, Bearer header, error parsing |
| `src/lib/schemas.ts` | Zod form schemas mirroring the Pydantic rules |
| `src/context/AuthContext.tsx` | JWT in localStorage, current user, logout on 401 |
| `src/hooks/useRegistrationActions.ts` | Register / cancel mutations and cache refresh |
| `src/pages/` | `LoginPage`, `RegisterPage`, `EventsPage`, `EventDetailPage` |
| `src/components/` | `EventFormDialog`, `RegistrationForm`, `ConfirmDeleteDialog`, `Pagination`, `SeatsBadge`, `Layout` |
| `src/components/ui/` | Generated shadcn/ui components |

All server data goes through TanStack Query and every mutation invalidates the
queries it affects. Every API error's `detail` message is shown in a toast
(see `main.tsx`); business rules are enforced by the API, not the UI.
