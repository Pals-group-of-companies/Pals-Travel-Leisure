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

Setup steps are in [`frappe-app/README.md`](frappe-app/README.md). If the server is unreachable, visitors still see the tours from `data/*.json` and forms open WhatsApp.

**Without a server (`FRAPPE_URL` left empty).**
- Tours and vehicles come from `data/tours.json` and `data/vehicles.json`.
- Forms open WhatsApp with the visitor's answers filled in, addressed to +254 757 129 599.
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
