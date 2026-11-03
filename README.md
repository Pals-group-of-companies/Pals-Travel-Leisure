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

The site runs in two modes and picks one automatically.

**Connected mode (the live version on claude.ai).** Tours, vehicles and every booking request are stored in a real-time database. The admin can change prices, photos, descriptions, inclusions and exclusions, hide or delete trips, and see every request and every interested person. Changes show on the site instantly.

**Standalone mode (this repo on GitHub Pages or any web host).** There is no database, so:
- Tours and vehicles come from `data/tours.json` and `data/vehicles.json`. Edit those files and push to update the site.
- When a visitor sends any form, WhatsApp opens with all their answers filled in, addressed to +254 757 129 599.
- The admin page opens, but explains that saving needs a database.

To make the admin save changes on your own hosting, connect a database (for example the company's Frappe/ERPNext system, Firebase or Supabase). The places to wire it are the `boot` section (loading tours, vehicles and bookings) and the `patch`, `submit` and upload handlers in `index.html`.

## Admin login

- Open the footer link **Admin login**, or go to `/#admin`.
- Username `admin`, password `admin`.

**Important:** this login is checked in the browser, so anyone who reads the page code can see it. It keeps casual visitors out of the dashboard but is not real security. Before the site goes public, replace it with a proper login on the server side and change the password.

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
