# Pals Travel & Leisure website

The new website for Pals Travel & Leisure (palstravelleisure.co.ke): safaris and tours, car hire, travel services, school transport, a plan-your-own-trip form, and an admin dashboard.

## What's in this repo

| Path | What it is |
|---|---|
| `index.html` | The whole website and admin in one file (HTML, CSS and JavaScript) |
| `assets/` | Logo, photos, vehicle images, icons and illustrations |
| `data/tours.json` | The safaris shown on the site (titles, photos, prices, itineraries, inclusions) |
| `data/vehicles.json` | The car hire fleet |
| `robots.txt`, `sitemap.xml`, `llms.txt` | Search engine and AI assistant files |

## Run it on your computer

The site loads its data with `fetch`, so open it through a small local server rather than double-clicking the file:

```bash
cd Pals-Travel-Leisure
python3 -m http.server 8000
# then open http://localhost:8000
```

## Put it online with GitHub Pages

1. Push this folder to `Pals-group-of-companies/Pals-Travel-Leisure` (commands below).
2. In the repo: **Settings → Pages → Deploy from a branch → `main` / root**.
3. To use palstravelleisure.co.ke, add the domain under **Settings → Pages → Custom domain** and point the domain's DNS to GitHub Pages.

## How bookings and the admin work

The site picks one of three modes automatically:

**With the Frappe server (the normal setup).** Set `FRAPPE_URL` at the top of the script in `index.html`. The `pals_website` app on your Frappe/ERPNext server then does the following:
- checks the admin sign-in.
- stores the safaris, the car hire fleet, photos and every booking request.
- shows changes the admin makes on the website straight away.

Setup steps are in [`frappe-app/README.md`](frappe-app/README.md). If the server is unreachable, visitors still see the tours from `data/*.json` and forms open an email to the right inbox, with WhatsApp as a backup.

**Without a server (`FRAPPE_URL` left empty).**
- Tours and vehicles come from `data/tours.json` and `data/vehicles.json`.
- Without the server, forms open an email with the visitor's answers: booking forms to reservations@palstravelleisure.co.ke, and general enquiries, careers and Pals Ambassadors to info@palstravelleisure.co.ke. A button also sends the same message on WhatsApp to +254 722 331 204.
- Every request carries a `sendTo` field with the same address, so the Frappe server can route it.
- The festive season holiday packages (prices in KES) are set in `PKG` inside `index.html`.
- The admin can't sign in.

**On claude.ai.** Data is stored in the artifact's database. Editing needs edit access to the artifact.

## Admin

- Open `https://palstravelleisure.co.ke/admin2`. There is no link to it anywhere on the website.
- Sign in with the Frappe account that has the **Pals Website Manager** role (see `frappe-app/README.md`). Frappe checks the password on the server. Nothing secret is stored in the website code.

## Push this folder to GitHub

```bash
cd Pals-Travel-Leisure
git init
git add .
git commit -m "New Pals Travel & Leisure website"
git branch -M main
git remote add origin https://github.com/Pals-group-of-companies/Pals-Travel-Leisure.git
git push -u origin main
```

If the repo already has files, run `git pull origin main --allow-unrelated-histories` before pushing.

## Before launch

- Set prices for every safari and vehicle.
- Replace the small photos in `assets/` with full-size originals (keep the same file names).
- Fill in inclusions, exclusions and booking terms for each safari.
- Give each page its own address (for example `/safaris`, `/car-hire`) so search engines can list them separately. `sitemap.xml` already uses these addresses.

## November 2026 redesign

- Text-only hero with a trip planner: pick what you are planning, a date and the number of travellers, and the matching enquiry form opens with them filled in.
- New pages: **Business** (business travel and events, business set-up and appointments, investor site visits) and **Careers** (jobs, and the Pals Ambassadors paid referral programme for students). Old `#diaspora` links open Careers.
- All enquiry forms open as a centred window.
- Language switcher for English, Chinese, Russian and Arabic (Arabic switches to right-to-left). Translations are built into `index.html`; names, phone numbers and emails stay as written. The admin dashboard stays in English.
- On the claude.ai live version, text the admin adds or edits is translated automatically with Claude. On a Frappe server, new tour text shows in English until a translation is added.
- Partner logos live in `assets/partners/`. All images were recompressed (about 6 MB to 2.6 MB).

## Languages, currency, legal and consent (November 2026)
- **Languages:** English plus Kiswahili, French, Spanish, German, Italian, Portuguese, Chinese, Russian and Arabic. Translations live in `i18n/<lang>.json` and load only when a visitor picks that language (or their browser asks for it). Rebuild them with `tr/build.py`. New safaris added by an admin are machine-translated into all nine languages automatically.
- **Currency:** prices are set in KES. The site guesses the visitor's currency from their time zone and converts at live rates from open.er-api.com (cached 12 hours), with built-in fallback rates. Visitors can change currency in the language menu.
- **Package add-ons:** optional extras and their per-person prices are in `data/addons.json` (public site) and editable in Admin > Add-ons & prices (database mode).
- **Legal pages:** `#legal/privacy`, `#legal/terms`, `#legal/cookies`, `#legal/bookings`, `#legal/accessibility` (also reachable at `/legal/...`). Have a Kenyan advocate review them before relying on them.
- **Cookie consent:** only strictly necessary browser storage is used by default. Google Maps on hotel pages loads only after consent. Fonts are self-hosted in `assets/fonts` (no Google Fonts request).
- **Clean URLs:** `vercel.json` serves `/safaris`, `/car-hire`, `/stay/<hotel>`, `/legal/<page>` etc. from `index.html`, and sets long cache headers for `assets/`.
