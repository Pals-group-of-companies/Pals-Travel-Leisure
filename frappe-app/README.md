# Pals Website app for Frappe / ERPNext

This small Frappe app is the website's server. It:

- checks the admin's sign-in. Frappe checks the password, stores it hashed, and blocks repeated wrong guesses.
- stores the safaris and the car hire fleet. The admin edits them from the website dashboard.
- stores every booking request a visitor sends. You see them in the dashboard and in Frappe under **Pals Booking Request**.
- stores photos the admin uploads, as public Frappe files.

It works on Frappe v14 and v15.

## On Frappe Cloud (palsgroup.frappe.cloud)

Frappe Cloud only installs custom apps on a **private bench** (shared plans can't run custom apps or server scripts). If the site is on a shared plan, move it to a private bench first (Frappe Cloud dashboard → Site → Move to a private bench).

1. **Put the app in its own GitHub repository.** Frappe Cloud needs the app at the root of a repo. Create e.g. `Pals-group-of-companies/pals_website` and copy the contents of `frappe-app/pals_website/` into it (so `pyproject.toml` is at the top).
2. **Add it to the bench.** Frappe Cloud → Benches → your bench → Apps → Add App → *Add from GitHub* → pick the repo, branch `main`. Deploy the bench.
3. **Install it on the site.** Sites → palsgroup.frappe.cloud → Apps → Install App → `pals_website`.
4. **Give the website its own admin address on your domain.** Sites → palsgroup.frappe.cloud → Domains → Add domain → `admin.palstravelleisure.co.ke`, then add the CNAME record Frappe Cloud shows you at your DNS provider. The sign-in cookie only works when the website and Frappe share the same main domain, so the website itself must be live on `palstravelleisure.co.ke` (not only on `vercel.app`).
5. **Site config** (Sites → palsgroup.frappe.cloud → Site Config → Add config):
   - `allow_cors` = `["https://palstravelleisure.co.ke", "https://www.palstravelleisure.co.ke"]`
   - optional `anthropic_api_key` = your Claude API key, to translate new safaris automatically into the nine other languages (optional `anthropic_model`, default `claude-haiku-5-5`).
6. **Create the admin user** as in step 3 below, then set `FRAPPE_URL = 'https://admin.palstravelleisure.co.ke'` in `index.html` (step 4 below).

## Timed safaris and add-on prices

- In the website dashboard each safari has **Dates on sale** (Show from / Show until). Frappe stops sending a safari to visitors after its last day (Nairobi time) and before its first day; the website also hides it on its own. Admins still see every safari.
- **Add-ons & prices** in the dashboard are saved in Frappe (`save_addons`) and sent to visitors with the catalogue.

## 1. Install the app on your Frappe server (self-hosted bench)

From your bench folder (replace `erp.palstravelleisure.co.ke` with your site name):

```bash
cp -r /path/to/Pals-Travel-Leisure/frappe-app/pals_website apps/
```

```bash
./env/bin/pip install -e apps/pals_website
```

```bash
grep -qx pals_website sites/apps.txt || echo pals_website >> sites/apps.txt
```

```bash
bench --site erp.palstravelleisure.co.ke install-app pals_website
```

```bash
bench restart
```

## 2. Let the website talk to Frappe

Allow the website's address to call the server:

```bash
bench --site erp.palstravelleisure.co.ke set-config --parse allow_cors '["https://palstravelleisure.co.ke", "https://www.palstravelleisure.co.ke"]'
```

**The Frappe site must be on a sub-domain of the website's domain**, for example `erp.palstravelleisure.co.ke` or `admin.palstravelleisure.co.ke`, and must use HTTPS. Browsers only send the admin's sign-in cookie between addresses on the same domain. If Frappe is on a different domain, signing in will look like it worked but every admin action will say "Your session ended".

## 3. Create the admin account

In Frappe go to **User → Add User**:

1. Enter the admin's email and name. Set **User Type** to **Website User**. The account can then use the website dashboard but not the Frappe desk.
2. Under **Roles**, tick **Pals Website Manager**.
3. Save. Under **Change Password**, set a strong password.

Any **System Manager** can also sign in to the website dashboard.

Wrong-password protection is under **System Settings → Login**. "Allow Consecutive Login Attempts" sets how many wrong tries are allowed before the account is locked for a while. The defaults are fine.

## 4. Point the website at Frappe

In `index.html`, near the top of the script, set:

```js
const FRAPPE_URL = 'https://erp.palstravelleisure.co.ke';
```

Push the change. Then open `https://palstravelleisure.co.ke/admin2` and sign in. The first time, the dashboard offers **Import tours and vehicles**. This copies `data/tours.json` and `data/vehicles.json` into Frappe once. From then on, edit everything from the dashboard.

## What visitors see if the server is down

The website still loads the tours and vehicles from `data/*.json`. Forms open WhatsApp instead, so no enquiry is lost.

## API (for developers)

All methods are in `pals_website/api.py` and are called as `/api/method/pals_website.api.<name>`.

| Method | Who | What |
|---|---|---|
| `get_catalog` (GET) | anyone | Tours and vehicles shown on the site (admins also get hidden ones) and who is signed in |
| `whoami` (GET) | anyone | The signed-in user and whether they are a website admin |
| `submit_request` (POST) | anyone, max 20 per hour per IP | Save a booking / enquiry |
| `get_requests` (GET) | admin | All booking requests |
| `set_request_status` (POST) | admin | new / contacted / confirmed / cancelled |
| `save_item` (POST) | admin | Create or update a tour or vehicle |
| `delete_item` (POST) | admin | Delete a tour or vehicle |
| `import_items` (POST) | admin | One-time copy of the JSON data files |
| `upload_image` (POST) | admin | Upload a JPG/PNG/WebP/GIF up to 10 MB |
| `save_addons` (POST) | admin | Package add-on prices per person in KES (`null` = price on request) |
| `translate_item` (background job) | system | Translates a saved safari into the other nine languages when `anthropic_api_key` is set |
