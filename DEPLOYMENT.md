# Put the portfolio online and manage it

## Recommended setup

Use **one Render Web Service**, built from the root `Dockerfile`. It runs the React website and FastAPI API on the same HTTPS domain. Google cookies and `/api` requests stay on that domain. Blog/About files are read from and committed to GitHub, so hosting restarts do not lose content.

You need a GitHub account, a Render account, and a Google Cloud project. Start with a Render Free service if its limits suit you: it sleeps after 15 minutes without inbound traffic, and a subsequent visit has to wait for it to wake. Choose a paid instance if you need it to stay awake. Check [Render's current free-service limits](https://render.com/docs/free) before selecting a plan.

Vercel supports FastAPI, but the Render Docker setup prepared here is the simplest path for this repository. Uploading just `frontend/` to Vercel would still leave its `/api` backend unconfigured. Follow the single-service steps below for the complete application.

**No live deployment has been created by these changes.** The root Dockerfile and production routes are prepared; you must connect your accounts and enter secrets in the hosting dashboard. Your computer can be turned off once the hosted service is live.

## 1. Make this folder its own Git repository

This workspace was found inside a parent Git repository at `D:\Coding\Programming`, with a remote pointing to `GreenHealth`. Do not push that parent repository as your portfolio.

In a PowerShell terminal, run:

```powershell
Set-Location 'D:\Coding\Programming\AI_python\mywebsite'
git init -b main
git rev-parse --show-toplevel
```

The last command must show **`D:/Coding/Programming/AI_python/mywebsite`**, not `D:/Coding/Programming`. This initializes Git metadata inside the portfolio folder without changing the parent repository. If this folder already has its own repository by the time you follow this guide, keep that repository and check its branch/remote instead.

At [GitHub's new repository page](https://github.com/new), create an empty repository named **`pranav-portfolio`** under **`CappyCap17`**. Leave README, license, and .gitignore initialization unchecked because the files already exist here. Public or private both work; private keeps Markdown drafts and history private at the repository level.

Back in PowerShell:

```powershell
git add .
git status --short
```

Confirm only portfolio source files are listed. `.env`, `.venv/`, `.tools/`, `node_modules/`, and `dist/` must not appear. Then:

```powershell
git commit -m "Build personal portfolio"
git remote add origin https://github.com/CappyCap17/pranav-portfolio.git
git push -u origin main
```

Complete GitHub's browser sign-in if Git Credential Manager asks. If Git requests author identity, set it locally in this repository using `git config user.name "Pranav Yerunkar"` and `git config user.email "YOUR_GITHUB_EMAIL"`, then retry the commit. Do not put tokens in the remote URL.

## 2. Create the token used by admin publishing

In GitHub:

1. Open your profile menu → **Settings** → **Developer settings**.
2. Open **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
3. Name it `portfolio-content`, select yourself as resource owner, and choose an expiration you can track.
4. Under repository access, select **Only select repositories** → `pranav-portfolio`.
5. Under repository permissions, set **Contents → Read and write**. Metadata read access is normally included automatically.
6. Generate the token. Copy it directly into Render's `GITHUB_TOKEN` secret setting in the next step. Do not commit it or send it in chat.

The token account must be allowed to commit directly to `main`. A branch rule requiring all changes through pull requests can prevent admin saves. When the token expires, replace its value in Render. See [GitHub's token instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## 3. Create the hosting service

1. Sign in at [Render](https://dashboard.render.com/) and connect GitHub.
2. Choose **New → Web Service** and select `CappyCap17/pranav-portfolio`. Grant Render access if the repository is private.
3. Set these fields:

| Render setting | Value |
| --- | --- |
| Name | `pranav-portfolio` or an available name you like |
| Branch | `main` |
| Runtime / Language | `Docker` |
| Root Directory | Leave blank |
| Dockerfile Path | `./Dockerfile` — the file at the project root |
| Docker Build Context | `.` if the field is shown |
| Docker Command | Leave blank; the Dockerfile supplies it |
| Health Check Path | `/api/health` |
| Instance type | Free to try it, or your chosen paid plan |

Do not select `frontend/Dockerfile` or `backend/Dockerfile` for this one-service deployment. No database or persistent disk is needed. Render builds React inside Docker, and the Python process serves the result on Render's `PORT`.

### Add environment variables before deploying

Generate a session secret locally:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into Render's `SESSION_SECRET`. Then enter:

| Key | Value |
| --- | --- |
| `CONTENT_STORAGE` | `github` |
| `COOKIE_SECURE` | `true` |
| `SESSION_SECRET` | The random value just generated |
| `ADMIN_EMAIL` | Your exact Google account email |
| `GITHUB_TOKEN` | The fine-grained token from step 2 |
| `GITHUB_OWNER` | `CappyCap17` |
| `GITHUB_REPO` | `pranav-portfolio` |
| `GITHUB_BRANCH` | `main` |

Click **Create Web Service / Deploy**. After the first deployment, copy the actual HTTPS URL shown by Render. Do not assume the example service name is available.

For the remaining examples, `https://YOUR-SITE.onrender.com` means that actual URL. Under your service's **Environment**, add:

```dotenv
FRONTEND_URL=https://YOUR-SITE.onrender.com
CORS_ORIGINS=https://YOUR-SITE.onrender.com
GOOGLE_REDIRECT_URI=https://YOUR-SITE.onrender.com/api/auth/callback
```

Use no trailing slash for the first two values. Save and redeploy when prompted. Google login stays unavailable until step 4; public pages can load in the meantime.

Render settings are independent from your local `.env`. Keep localhost values in the local `.env` for development. Do not upload that file.

References: [Render Docker deployment](https://render.com/docs/docker), [web-service configuration](https://render.com/docs/web-services).

## 4. Enable Google login and your admin account

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create/select a project, such as `Pranav Portfolio`.
2. Open **Google Auth Platform** (or **APIs & Services → OAuth consent screen**).
3. Configure the app name, support email, and developer contact email. Choose an external audience for a normal personal Google account.
4. If the app is in Testing mode, add your own Google email under **Audience → Test users**. This is sufficient to begin testing your admin login. Configure/publish the audience when you want general visitor login, following any requirements Google shows.
5. Go to **Clients → Create client**, or **Credentials → Create credentials → OAuth client ID**.
6. Choose **Web application** and give it a name.
7. Add this authorized JavaScript origin:

   ```text
   https://YOUR-SITE.onrender.com
   ```

8. Add this **Authorized redirect URI**, exactly:

   ```text
   https://YOUR-SITE.onrender.com/api/auth/callback
   ```

9. Create the client. Copy the client ID and client secret into Render:

   ```dotenv
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

10. Verify Render's `ADMIN_EMAIL` is the exact email of the Google account you will use. The comparison is case-sensitive; there is no separate admin password or registration step.
11. Save environment settings and redeploy. Keep `SESSION_SECRET` unchanged between deploys.

For local login too, add `http://localhost:5173` as another origin and `http://localhost:5173/api/auth/callback` as another redirect URI. Put the corresponding credentials and your admin email in local `.env`, then restart the local backend. Keep local `COOKIE_SECURE=false` for HTTP.

Google requires the callback to match its configured redirect URI exactly. See [Google's web-server OAuth instructions](https://developers.google.com/identity/protocols/oauth2/web-server).

## 5. Open and use your admin panel

Open the site in a normal browser such as Chrome or Edge (Google may reject login inside embedded IDE browsers).

1. Visit **`https://YOUR-SITE.onrender.com/login`**.
2. Click **Continue with Google** and choose the account matching `ADMIN_EMAIL`.
3. Open **Admin** in the sidebar, or visit **`https://YOUR-SITE.onrender.com/admin`** directly.

Other Google users may sign in when your Google configuration allows it, but they cannot access admin functions. Visitors can read your projects, published posts, and About page without signing in.

### Publish a blog post

1. In `/admin`, choose **New blog post**.
2. Fill in title, slug (e.g. `my-first-project`), date, and summary.
3. Write the Markdown body. Use **Preview** to check it.
4. Check **Published — visible to everyone**.
5. Click **Save & publish** and wait for the success message.
6. Follow **View GitHub commit** to confirm the save, or open `/blog` to read the post.

There is no manual deployment step for blog publishing. The backend reads the repository on the next content request. A public tab already open before your edit needs a refresh.

### Draft, edit, unpublish, or delete

- **Draft:** leave Published unchecked and choose Save draft. It is hidden from the public site. If the GitHub repository is public, its Markdown and commit history are still public.
- **Edit:** choose the pencil icon beside a post in `/admin`, make changes, and save.
- **Unpublish:** edit the post, uncheck Published, and save. Its public URL stops serving the article.
- **Delete:** click the trash icon in `/admin` and confirm. It deletes the Markdown file with a Git commit; earlier versions remain in Git history.
- **Slug:** set this carefully when creating the post. Existing slugs are locked so editing a title does not silently break links.
- **Conflict:** if another edit changed the file after you loaded it, copy any unsaved text, reload, and apply your changes to the newest version.

### Change About Me

1. Open `/admin` → **Edit about me**.
2. Edit the Markdown and preview it.
3. Click **Save about page**.
4. Visit `/about` to check it. This updates `content/about.md` in GitHub.

## 6. What you change where

| What you want to change | Where to change it | Deployment needed? |
| --- | --- | --- |
| Blog title, date, summary, text, visibility | Admin → edit post | No |
| About page text | Admin → Edit about me | No |
| Projects shown | Your public GitHub repositories | No; project cache refreshes after about five minutes |
| Project descriptions, language, homepage/demo link | The individual repository on GitHub; language is detected by GitHub | No, after cache refresh |
| Name, contact email, LinkedIn, short heading bio | `frontend/src/config/site.ts` | Yes, commit/push |
| Wallpaper | Add/replace `frontend/public/background.jpg` | Yes, commit/push |
| Colors, fonts, spacing, glass panels | `frontend/src/styles.css` | Yes, commit/push |
| Navigation, page layout, new functionality | React source under `frontend/src/` | Yes, commit/push |
| Admin email, tokens, OAuth credentials | Render → Environment | Save/redeploy as prompted |
| Custom domain | Render → Settings → Custom Domains, then your DNS provider | Follow Render's domain setup |

The admin panel currently edits **blog posts and About content only**. It has no wallpaper uploader, contact settings editor, repository curator, or visual theme editor. Images in Markdown can use HTTPS image URLs or assets you commit into `frontend/public/`.

Example contact configuration:

```ts
email: 'your-address@gmail.com',
linkedinUrl: 'https://www.linkedin.com/in/your-profile/',
```

### Apply future source-code changes

Admin publishing creates commits on GitHub, so pull those commits before editing locally. With a clean working tree:

```powershell
git pull --ff-only origin main
```

Edit your files, then:

```powershell
git add .
git commit -m "Update portfolio details"
git push origin main
```

With Render auto-deploy enabled, source pushes trigger a new deployment. Watch its Deploys/Events logs until the new build is live. Content commits can also trigger an automatic build, although the blog/About update does not depend on that build. Optionally configure Render's build filters to ignore `content/**` so content-only commits do not rebuild the service.

Do not force-push to resolve a rejected push: your online admin edits may be the new commits you need to pull first.

## 7. Check the deployed result

Visit these URLs using the actual public domain:

1. `/api/health` → `{"status":"ok","storage":"github"}`.
2. `/projects` → live repository cards.
3. `/blog` and `/about` → content from your GitHub repository.
4. `/login` → Google login completes and returns to the site.
5. `/admin` → accessible for your configured account.
6. Create an unpublished test draft, confirm it is absent from `/blog`, publish it, then confirm it appears. Unpublish or delete it afterward if desired.
7. Open an incognito window without logging in: public pages should work, and `/admin` should send you to Login.
8. Refresh a deep URL such as `/blog/hello-world` directly; the React page should still load.

If using a custom domain later, update `FRONTEND_URL`, `CORS_ORIGINS`, `GOOGLE_REDIRECT_URI`, and Google's authorized origin/callback to that domain, then sign in again there.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| First visit is slow | A Render Free service may be waking up. Check its logs and service status. |
| Docker deployment fails | Select the root `./Dockerfile`, leave Root Directory blank, and check build logs. `frontend/package-lock.json` must be committed. |
| Service fails at startup | Check `SESSION_SECRET` is at least 32 random characters when `COOKIE_SECURE=true`. |
| Google button unavailable | Set both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`, then redeploy. |
| Google reports redirect URI mismatch | Match the full HTTPS callback exactly in Render and Google, including `/api/auth/callback`. |
| Google login denied in IDE preview | Open the deployed URL in a regular browser. |
| Signed in, but no Admin link | Check the exact `ADMIN_EMAIL` and selected Google account. |
| Save fails with CSRF/origin error | Set the site's exact public origin in `CORS_ORIGINS` and `FRONTEND_URL`; sign out/in after changing it. |
| Blog/About fails to load | Check GitHub owner/repo/branch/token and ensure `content/` was pushed. |
| Save fails with GitHub permissions/conflict error | Check token expiration, Contents write permission, branch rules, and whether the file was edited elsewhere. |
| Local `git push` is rejected after admin publishing | Pull the new content commits, resolve any conflicts, then push normally. |

## What was verified locally

The single-service entry point is tested for React deep links, API routing, missing assets, and security headers. The existing content and authorization regression suite is also run. Docker Engine was unavailable during preparation, so the image build and the actual Render deploy still need to complete on Render. Live Google OAuth and GitHub writes require your account credentials.
