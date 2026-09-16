# Pranav Yerunkar · Personal portfolio

A responsive glass dashboard with live GitHub projects, a Markdown blog, an editable About page, Google sign-in, and a private content studio. React + TypeScript + Vite + Tailwind on the frontend; FastAPI, Authlib, and httpx on the backend. No database or account persistence.

**Ready to put it online? Follow [DEPLOYMENT.md](DEPLOYMENT.md) for the complete Render, Google login, GitHub publishing, and admin walkthrough.** The root `Dockerfile` hosts both parts on one domain. The separate Docker Compose setup remains available for local use.

## Quick start

Prerequisites: Node.js 22+, Python 3.12+, and optionally Docker Compose. Run commands from the project root unless noted.

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another:

```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to FastAPI. Public pages run without OAuth or GitHub credentials in local storage mode. Projects require internet access to GitHub.

On macOS/Linux, use `cp .env.example .env` and `.venv/bin/python` instead of the Windows equivalents.

This workspace also includes an ignored portable Node installation at `.tools/node-v22.16.0-win-x64` if Node is absent from PATH. To use it from the root in PowerShell:

```powershell
$env:PATH = (Join-Path (Get-Location).Path '.tools/node-v22.16.0-win-x64') + ';' + $env:PATH
```

## Frontend commands

Run in `frontend/`:

```text
npm run dev        # development server
npm run typecheck  # strict TypeScript check
npm run build      # TypeScript check and production build
npm run preview    # preview production assets (use Docker for API proxying)
```

## Content and architecture

```text
frontend/src/config/site.ts   Name, biography, GitHub, email, LinkedIn
frontend/src/styles.css      Glass panels, layout, responsive styles
frontend/src/pages/          Public pages and admin editors
frontend/public/             Static assets and optional background.jpg
backend/app/main.py          HTTP API, OAuth, admin authorization
backend/app/storage.py       Shared local/GitHub storage contract
backend/app/config.py        Backend-only environment settings
content/blog/*.md            Blog frontmatter and Markdown
content/about.md             About Markdown
backend/tests/               API and storage regression tests
```

The browser always reads content through FastAPI. In `github` mode, reads fetch the configured repository branch directly and writes use the GitHub Contents API. Saving returns a commit link; navigating to the public blog fetches the latest content immediately, with no rebuild or deployment. GitHub content is intentionally uncached to avoid stale posts across workers. Repository cards use a five-minute in-memory cache with stale results if GitHub fails; cold failures show a retry state.

In `local` mode, edits replace files atomically in `content/`. Run one backend worker in this development mode. GitHub edits use file SHAs as revisions; stale edits return a conflict instead of silently overwriting newer changes. Existing slugs are immutable; create a new post to use a new slug. Uncheck Published and save to unpublish, or delete from the dashboard.

Blog files must have a filename matching their slug:

```markdown
---
title: "A new idea"
slug: "a-new-idea"
date: "2026-09-15"
summary: "A short description."
published: true
---

Your Markdown here.
```

Slugs accept lowercase letters, numbers, and single hyphens. Markdown supports fenced code, tables, links, and responsive images. Raw HTML is not enabled. The initial About text and welcome post are starter copy for you to personalize.

## Environment settings

Create `.env` from `.env.example`. It is ignored by Git and Docker build contexts. Never put secrets in `VITE_*` variables or frontend files.

| Variable | Purpose |
| --- | --- |
| `CONTENT_STORAGE` | `local` for development; `github` for production publishing |
| `SESSION_SECRET` | At least 32 random characters; mandatory with secure cookies. Blank in development generates an ephemeral key and restarts sign everyone out. |
| `COOKIE_SECURE` | `false` for localhost HTTP; `true` for production HTTPS |
| `FRONTEND_URL` | Exact public origin, without a trailing slash, e.g. `https://portfolio.example.com` |
| `CORS_ORIGINS` | Comma-separated exact allowed browser origins, normally the same as `FRONTEND_URL` |
| `GOOGLE_CLIENT_ID` | Google OAuth web application client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret, backend-only |
| `GOOGLE_REDIRECT_URI` | Exact public callback, e.g. `http://localhost:5173/api/auth/callback` |
| `ADMIN_EMAIL` | Exact, case-sensitive verified Google email allowed to edit content |
| `GITHUB_TOKEN` | Fine-grained token for the content repository, backend-only |
| `GITHUB_OWNER` | Repository owner and public projects username; defaults to `CappyCap17` |
| `GITHUB_REPO` | Repository name containing this project's `content/` directory |
| `GITHUB_BRANCH` | Existing writable content branch, defaults to `main` |

Generate a session secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste it into `.env`. Use the same secret across production instances.

## Google OAuth

1. In Google Cloud Console, create/select a project and configure its OAuth consent screen (Google Auth Platform branding, audience, and data access).
2. Create an OAuth client of type **Web application**.
3. Add `http://localhost:5173` as an authorized JavaScript origin and `http://localhost:5173/api/auth/callback` as an authorized redirect URI. Add your exact HTTPS production equivalents when deploying.
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, and `ADMIN_EMAIL` in `.env`, then restart FastAPI.
5. While the Google app is in testing, add allowed Google accounts as test users. Publish the consent configuration to admit general visitors as appropriate for your Google project.

Authlib validates OAuth state and OpenID Connect tokens. The callback requires a verified email. Sessions are signed (not encrypted), HttpOnly, SameSite=Lax cookies expiring after eight hours of inactivity. Only name, email, picture, and a CSRF token remain in the session after login. Google access tokens are not retained. Every admin endpoint independently checks the exact email; frontend guards are for navigation only. Mutations also require the session CSRF token and an allowed Origin. Logout clears the cookie; stateless sessions have no server-side per-session revocation list.

## GitHub publishing

1. Push this project, including `content/`, to your GitHub repository and make sure `GITHUB_BRANCH` exists.
2. Create a fine-grained personal access token restricted to that repository with **Contents: Read and write** permission.
3. Set `CONTENT_STORAGE=github`, `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, and `GITHUB_BRANCH` in the backend environment.
4. Ensure branch rules permit direct commits by the token owner. Restart the backend, sign in with `ADMIN_EMAIL`, and open `/admin`.
5. Write, preview, and save. The success message links to the resulting GitHub commit. The next public read sees the change directly.

Do not use production filesystem mode on ephemeral or read-only hosts. GitHub mode does not write content files on the server. Back up your repository and review its commit history for content changes. If your host automatically redeploys on every commit, optionally configure it to ignore content-only changes; the site does not need that rebuild.

Implementation references: [GitHub Contents API](https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28) and [Authlib Starlette OAuth](https://docs.authlib.org/en/latest/client/starlette.html).

## Background and personal details

Add your actual wallpaper at `frontend/public/background.jpg`. The CSS loads it over a simple sunset-colored gradient fallback. No synthetic wallpaper is included. In development Vite serves it immediately; rebuild the frontend for production. Adjust `background-position` in `frontend/src/styles.css` to change the crop.

Edit `frontend/src/config/site.ts` to add email and LinkedIn; unconfigured links display a clear unavailable state. If changing GitHub identity, also update `GITHUB_OWNER` in `.env`. Use the About editor for your biography content. Visual styles are centralized in `styles.css` for later reference/Figma changes.

## Docker

With Docker Engine running and `.env` present:

```text
docker compose config --quiet
docker compose up --build -d
docker compose logs -f
docker compose down
```

Open `http://localhost:5173`. Nginx serves the React build, handles client-side routes, and proxies `/api` to the internal FastAPI container. No database service is present. The local content bind mount preserves local development edits. Linux users should ensure that the mounted directory is writable by container UID 1000 for local mode. Remove the content mount for a production GitHub-mode deployment if desired.

For production, terminate HTTPS at your hosting proxy, use GitHub storage, set `COOKIE_SECURE=true`, a strong persistent `SESSION_SECRET`, and the correct HTTPS frontend origin and callback. Keep frontend and API on the same public origin so cookies work reliably. Only expose the frontend service. Nginx supplies security headers, a restrictive content policy, and a request size limit. Set a proxy request limit of 600 KB if deploying FastAPI behind a different proxy. Use persistent secret settings supplied by the host. Keep dependencies updated.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall -q backend/app
cd frontend
npm run build
```

Tests cover anonymous/visitor/admin authorization, exact email matching, CSRF and Origin rejection, published/draft visibility, create/update/unpublish/delete, stale revisions, About editing, slug/path validation, cookie flags, logout, GitHub failures, and mocked commit payloads. They use temporary local content, not the real blog. Google login and real GitHub commits need your credentials for end-to-end verification.

### Checks performed in this workspace

- Frontend dependency installation and production build passed; strict TypeScript passed. npm reported zero known dependency vulnerabilities at installation.
- Seven backend regression tests passed; Python dependency consistency and compilation passed.
- Running FastAPI endpoints served the blog, article, About, session, and health data. Live GitHub fetching returned 18 repositories.
- Headless Chrome checked seven public routes, anonymous admin redirect, live project search/sort, mobile navigation, and safe admin Markdown preview. No JavaScript exceptions or horizontal overflow were observed at the tested desktop/mobile sizes.
- `docker compose config --quiet` passed. Container builds/runtime were not tested because Docker Engine was stopped.
- OAuth exchange and actual GitHub content commits were not attempted without your credentials. The supplied background image remains to be added; the gradient fallback was inspected in Chrome.
