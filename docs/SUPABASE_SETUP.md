# Supabase Setup — 5 minutes, one-time

This is the only step that's a little fiddly, and it's only fiddly the first time. You're creating a free Supabase project that handles **sign-in** and **conversation storage** for your deployment. Without it, anyone with your URL could chat using your Anthropic key, which is exactly what we don't want.

If you've never used Supabase: it's a hosted database with auth built in. Free tier is generous (500MB database, ~50,000 active users/month). They take payment info but you don't get charged unless you blow past the free limits, which a personal chat tool almost certainly won't.

---

## Step 1: Create a Supabase project

1. Go to [supabase.com](https://supabase.com) → click **Start your project** (or **Sign in** if you already have an account).
2. Sign up with GitHub (it's the fastest path).
3. On the dashboard, click **New project**.
4. Pick an **organization** (your personal one is fine).
5. Fill in:
   - **Name:** anything you want, e.g. `beginner-api-interface`
   - **Database Password:** Supabase generates a strong one — click **Generate** and let it set one. **Save it somewhere safe** (password manager). You won't need it for this app, but you'll want it if you ever poke at your database directly.
   - **Region:** pick whichever is geographically closest to you (faster).
   - **Pricing Plan:** **Free**.
6. Click **Create new project**.

Wait ~1 minute. Supabase is provisioning your database. You'll see a "Setting up project…" screen.

---

## Step 2: Run the schema

Once the project is ready, you'll land on the project dashboard.

1. In the left sidebar, find the **SQL Editor** icon (looks like `</>`).
2. Click **+ New query** (or there may already be an empty editor open).
3. Open the file [`docs/supabase-schema.sql`](supabase-schema.sql) from this repo. Copy its **entire contents**.
4. Paste it into the Supabase SQL Editor.
5. Click **Run** (bottom right, or `Cmd/Ctrl + Enter`).

You should see "Success. No rows returned" or similar. If you see any red errors, read them carefully — usually it's a copy-paste issue. The schema is safe to re-run; it uses `IF NOT EXISTS` everywhere.

That schema creates three tables (projects, conversations, files) and locks them down so each user can only see their own rows. Without that lock-down (Row-Level Security), one user could read another's conversations.

---

## Step 3: Grab the values you need

You need three values from your Supabase project to put into Vercel:

1. **Supabase URL** and **anon key**: in the left sidebar, click the gear icon (**Project Settings**) → **API**. Look for:
   - **Project URL** — looks like `https://xxxxxxxxxxxxx.supabase.co`. Copy it.
   - **anon / public key** — a long string starting with `eyJ`. Copy it.
2. **JWT Secret**: still in **Project Settings → API**, scroll down to **JWT Settings** → **JWT Secret**. Click the eye icon to reveal, then copy it.

Keep all three open in a notepad — you'll paste them into Vercel in the next step.

> **A note on the keys:** the **anon key** is designed to be public (it's shipped to every browser that loads your app). The **JWT secret** is **NOT** — keep it private. The schema's row-level security policies are what actually protect data, even though the anon key is public.

---

## Step 4: Add the values to Vercel

If you've already deployed to Vercel:

1. Go to [vercel.com](https://vercel.com) → your project → **Settings → Environment Variables**.
2. Add these three:
   - **Name:** `SUPABASE_URL`     — **Value:** the Project URL from Step 3
   - **Name:** `SUPABASE_ANON_KEY` — **Value:** the anon key from Step 3
   - **Name:** `SUPABASE_JWT_SECRET` — **Value:** the JWT Secret from Step 3
3. Make sure they're available for **Production** (and Preview if you want).
4. Go to **Deployments** → most recent → ⋯ → **Redeploy**.

If you're deploying for the first time, you'll add these on Vercel's "Configure Project" screen along with `ANTHROPIC_API_KEY` (so 4 environment variables total).

---

## Step 5: Configure the magic-link redirect (recommended)

When someone signs in, Supabase sends them an email with a magic link. That link sends them back to your app — but Supabase only allows redirects to URLs you've pre-approved.

1. Supabase dashboard → **Authentication** (left sidebar) → **URL Configuration**.
2. **Site URL:** set this to your Vercel deployment URL, e.g. `https://your-project.vercel.app`.
3. **Redirect URLs:** add both:
   - `https://your-project.vercel.app`
   - `https://your-project.vercel.app/*`
   - (And `http://localhost:3000` if you use `vercel dev` locally.)
4. Click **Save**.

Without this, magic-link emails will go out but clicking them will dump people on Supabase's default landing page instead of your app.

---

## Done

Open your deployed URL. You should see a sign-in screen. Enter your email, hit **Send link**, check your inbox, click the link, and you're in.

Each signed-in user gets their own private space — their projects, conversations, and files are visible only to them. Open the app on your phone, sign in with the same email, and you'll see all the same conversations. That's the cross-device sync, free.

---

## Common gotchas

**"Setup needed" screen on the deployed app.** That means `/api/config` returned `configured: false` — probably one or both of `SUPABASE_URL` / `SUPABASE_ANON_KEY` is missing or named wrong in Vercel. Check Vercel → Settings → Environment Variables, then redeploy.

**Magic link email never arrives.** Check spam first. If still missing: Supabase → Authentication → Email templates — you can verify the email service is enabled. The free tier has rate limits (3 emails per hour by default for unauth users); usually fine for personal use.

**Magic link arrives but clicking it doesn't sign me in.** You probably skipped Step 5. The redirect URL has to be on Supabase's allow-list.

**"Authentication required" when sending a chat.** Your `SUPABASE_JWT_SECRET` env var isn't matching the one in your Supabase project. Re-copy it from Supabase Settings → API → JWT Secret, paste into Vercel, redeploy.

**I want to start over with a fresh database.** Supabase dashboard → Project Settings → General → scroll to **Pause project** or **Delete project**. Or just drop the tables in SQL Editor: `DROP TABLE files; DROP TABLE conversations; DROP TABLE projects;` then re-run the schema.
