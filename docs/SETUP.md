# Setup Guide — From Zero to Running

This guide assumes you've never deployed to Vercel and have only basic GitHub experience. Follow it top to bottom and you'll have a working, **safe-by-default** chat interface in about 15 minutes.

By "safe-by-default" we mean: the deployed URL requires sign-in, conversations are private to each user, and a stranger who finds your URL can't spend your Anthropic credits. That protection comes from a piece called Supabase, which adds one extra setup step. It's worth the 5 minutes.

---

## What you'll need

Four free things — sign up before you start so you don't have to stop mid-deploy:

1. **A GitHub account** — sign up at [github.com](https://github.com) if you don't have one.
2. **A Vercel account** — sign up at [vercel.com](https://vercel.com) using **"Continue with GitHub"**. Vercel is what hosts the actual website.
3. **A Supabase account** — sign up at [supabase.com](https://supabase.com) using **GitHub**. Supabase handles sign-in and stores your conversations.
4. **An Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com/) → **Settings → API Keys → Create Key**.
   - **Important:** Anthropic charges per use. Add a small credit balance (~$5) at **Plans & Billing** before chatting; otherwise the API rejects requests.

Keep your API key somewhere safe (a password manager). It starts with `sk-ant-`.

---

## Step 1: Fork this repo

Forking = making your own copy of someone else's GitHub repo, under your account. Your copy is yours to change.

1. Make sure you're logged into GitHub.
2. At the top right of [the main repo page](https://github.com/crmccarthy79-ai/beginner-api-interface), click **Fork**.
3. Leave the defaults and click **Create fork**.
4. You'll land on YOUR copy. The URL says `github.com/YOUR_USERNAME/beginner-api-interface`.

---

## Step 2: Set up Supabase (one-time, ~5 min)

Open [`docs/SUPABASE_SETUP.md`](SUPABASE_SETUP.md) and follow it step-by-step. It walks you through:

- Creating a free Supabase project
- Running the SQL schema (one paste-and-click)
- Copying three values you'll need: **URL**, **anon key**, **JWT secret**
- (After deploy) configuring magic-link redirects

Come back here when you have those three values copied somewhere.

---

## Step 3: Deploy on Vercel

You have two paths. Pick whichever feels easier.

### Easy path — Deploy button

On your forked repo's README, click the orange **Deploy with Vercel** button. It pre-fills everything for you, then jumps to the env-vars step below.

### Manual path

1. Go to [vercel.com/new](https://vercel.com/new).
2. Find **beginner-api-interface** (your fork) and click **Import**.
   - First time only: Vercel will ask permission to read your GitHub repos. Allow it.

### The Configure Project screen (both paths land here)

3. Find the **Environment Variables** section and add **four** variables:

   | Name | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your Anthropic key (starts with `sk-ant-`) |
   | `SUPABASE_URL` | from Supabase → Settings → API → Project URL |
   | `SUPABASE_ANON_KEY` | from Supabase → Settings → API → anon key |
   | `SUPABASE_JWT_SECRET` | from Supabase → Settings → API → JWT Secret (under JWT Settings) |

4. Click **Deploy**.
5. Wait ~30 seconds. You'll see a confetti animation when it's done.
6. Click **Continue to Dashboard**, then click your project name. The production URL is at the top of the project Overview page (something like `your-project-xyz.vercel.app`). Click it to open your live site.

---

## Step 4: Tell Supabase about your URL

You need to tell Supabase that magic-link emails are allowed to redirect to your new Vercel URL. Without this, sign-in won't complete.

1. Supabase dashboard → your project → **Authentication** (left sidebar) → **URL Configuration**.
2. **Site URL:** paste your Vercel URL.
3. **Redirect URLs:** add `https://your-project-xyz.vercel.app` and `https://your-project-xyz.vercel.app/*`.
4. **Save**.

(See [`SUPABASE_SETUP.md` Step 5](SUPABASE_SETUP.md#step-5-configure-the-magic-link-redirect-recommended) for screenshots of what to look for.)

---

## Step 5: Sign in and chat

Open your Vercel URL. You'll see a sign-in screen.

1. Enter your email and click **Send link**.
2. Check your inbox (and spam) for an email from Supabase. Click the link.
3. You're back at your app, signed in.
4. A first project is auto-created. Click the project name at the top to rename it.
5. Type a message in the box at the bottom and press **Enter**.

If you get this far, **you're done**. Your deployment is safe to share — anyone who knows the URL can see the sign-in screen, but only people who actually sign in can use it.

---

## Step 6: Want a *more* private deployment? (optional)

By default, anyone with your URL can sign up and use the app — they'll spend credits on the API call, but they need to be signed in (which gives you their email). If you want the deployment locked to *just specific people*, two options:

- **In Supabase:** Authentication → Settings → toggle off **Enable email signups**. Then in Authentication → Users, manually invite specific email addresses. Now only invited users can sign in.
- **Set an Anthropic spending cap** at [console.anthropic.com](https://console.anthropic.com/) → Plans & Billing. Caps your blast radius if anything goes sideways.

---

## Common gotchas

**"Setup needed" screen.** Your Supabase env vars are missing or wrong in Vercel. Settings → Environment Variables → check `SUPABASE_URL` and `SUPABASE_ANON_KEY`, then redeploy.

**Magic link arrives but clicking it doesn't sign me in.** You skipped Step 4. Add your URL to Supabase's redirect allow-list.

**500 error or "Authentication required" when sending a message.** Either `ANTHROPIC_API_KEY` is missing/wrong, or `SUPABASE_JWT_SECRET` doesn't match the one in your Supabase project. Re-copy from Supabase → Settings → API and redeploy.

**"Insufficient credits."** Anthropic doesn't give free usage. Add a payment method at [console.anthropic.com](https://console.anthropic.com/) → Plans & Billing.

**I made a code change. How do I deploy it?** Push to your forked GitHub repo (commit + push to `main`). Vercel auto-deploys whenever you push. Takes about 30 seconds.

---

## What next?

- **Customize colors** — `public/styles.css`, the `:root` section near the top.
- **Default model / system prompt** — `public/app.js`, the constants near the top.
- **Add or remove models** — the `MODELS` array in `public/app.js`.
- **Use Claude Code to make changes** — open the repo folder, run `claude`, describe what you want changed. See the README's "Customizing" section.

---

## Local development (optional)

```bash
git clone https://github.com/YOUR_USERNAME/beginner-api-interface.git
cd beginner-api-interface

# Create a .env file with all four keys
cat > .env <<EOF
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=...
EOF

# On macOS with Homebrew Python, install uv first:
brew install uv

# Then:
npx vercel dev
```

Add `http://localhost:3000` to your Supabase redirect URLs (Step 4) so magic links work locally too.

---

## Stuck?

Open an issue on the [original repo](https://github.com/crmccarthy79-ai/beginner-api-interface/issues) with the exact step you got stuck on and what you saw.
