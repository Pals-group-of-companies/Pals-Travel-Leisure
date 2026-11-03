# Pals Website app for Frappe / ERPNext

This small Frappe app is the website's server. It:

- checks the admin's sign-in. Frappe checks the password, stores it hashed, and blocks repeated wrong guesses.
- stores the safaris and the car hire fleet. The admin edits them from the website dashboard.
- stores every booking request a visitor sends. You see them in the dashboard and in Frappe under **Pals Booking Request**.
- stores photos the admin uploads, as public Frappe files.

It works on Frappe v14 and v15.

## 1. Install the app on your Frappe server

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
