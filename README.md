# Matcha Mart Restock Alerts

Checks 7 specific matchamart.ca products every 10 minutes and emails
tarahouse999@gmail.com the moment one goes from sold out to in stock.

## How it works
- `products.json` — the list of product page URLs being watched
- `track_products.py` — fetches each product's Shopify `.json` data,
  compares availability to last run, emails on any restock
- `state.json` — remembers what was in/out of stock last time (the workflow
  commits updates to this file automatically, so don't edit it by hand)
- `check-stock.yml` — GitHub Actions workflow that runs the script on a timer

## One-time setup (about 10 minutes)

### 1. Create the GitHub repo
1. Go to github.com and create a new **private** repository (e.g. `matcha-alerts`).
2. Upload all the files from this folder to it, EXCEPT `check-stock.yml` —
   that one goes in a special folder:
   - Create a folder path `.github/workflows/` in the repo
   - Put `check-stock.yml` inside it, so the final path is
     `.github/workflows/check-stock.yml`
   - Everything else (`track_products.py`, `products.json`, `state.json`,
     `requirements.txt`) goes in the root of the repo.

   Easiest way: on your computer, put all files in a folder in this
   structure, then drag the whole thing into GitHub's "upload files" page,
   or use `git` from the command line if you're comfortable with it.

### 2. Get a free Resend account (for sending the email)
1. Go to https://resend.com and sign up using **tarahouse999@gmail.com**
   (must match, so their free sending address is allowed to email you).
2. Once logged in, go to **API Keys** and create a new key.
3. Copy the key — you'll only see it once.

### 3. Add your secrets to GitHub
1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret** and add:
   - Name: `RESEND_API_KEY` → Value: (the key you copied)
   - Name: `NOTIFY_EMAIL` → Value: `tarahouse999@gmail.com`

### 4. Turn it on
1. Go to the **Actions** tab in your repo.
2. You should see "Check Matcha Stock" listed. Click it.
3. Click **Run workflow** to trigger it manually once, just to confirm it
   works (check the run's logs — it should say "No restocks detected" since
   this is the first run and everything is currently marked sold out).
4. After that, it runs automatically every 10 minutes on its own — nothing
   else to do.

## Adding or removing products later
Just edit `products.json` in the GitHub repo (any matchamart.ca product page
URL works) and commit the change. No need to touch the script.

## Notes
- The first run never sends an alert (there's nothing to compare against
  yet) — it just records the current stock state as the baseline.
- If a product page URL is wrong or removed, the script logs an error for
  that one item and keeps checking the rest.
