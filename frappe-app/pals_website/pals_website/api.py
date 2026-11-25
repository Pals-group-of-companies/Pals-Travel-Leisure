"""API used by the Pals Travel & Leisure website (index.html).

Public (no login):
  get_catalog      tours and vehicles shown on the website
  submit_request   a visitor's booking / enquiry form
  log_client_error a JavaScript error from a visitor's browser (rate-limited)

Website admins only (role "Pals Website Manager" or "System Manager"):
  get_requests, set_request_status, save_item, delete_item,
  import_items, upload_image, save_addons

Timed safaris: a tour may carry "validFrom" and/or "validUntil" (YYYY-MM-DD,
Nairobi time, inclusive). Visitors only receive tours that are on sale now;
admins receive everything.

Translations: if site_config has "anthropic_api_key", every saved tour is
translated in the background into the website's nine other languages and the
result is stored in the tour's "tr" field, which the website uses directly.

Admins sign in with Frappe's own /api/method/login, so passwords are checked
and stored (hashed) by Frappe, and failed attempts are throttled by Frappe.
"""

import json
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

ROLE = "Pals Website Manager"
ITEM = "Pals Website Item"
REQUEST = "Pals Booking Request"
KINDS = ("tours", "vehicles", "packages")
STATUSES = ("new", "contacted", "confirmed", "cancelled")
MAX_JSON = 120_000  # characters (room for translations)
TZ = ZoneInfo("Africa/Nairobi")
LANGS = {"sw": "Swahili", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian", "pt": "Portuguese (Portugal)", "zh": "Simplified Chinese", "ru": "Russian", "ar": "Modern Standard Arabic"}
ADDONS_KEY = "pals_website_addons"
MAX_IMAGE = 10 * 1024 * 1024  # bytes
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# ---------- helpers ----------
def is_admin(user=None):
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if user == "Administrator":
		return True
	return bool({ROLE, "System Manager"} & set(frappe.get_roles(user)))


def _require_admin():
	if not is_admin():
		frappe.throw(_("Please sign in as a website admin."), frappe.PermissionError)


def _dict(value, what="data"):
	if isinstance(value, str):
		if len(value) > MAX_JSON:
			frappe.throw(_("The {0} is too large.").format(what))
		try:
			value = json.loads(value)
		except ValueError:
			frappe.throw(_("Invalid {0}.").format(what))
	if not isinstance(value, dict):
		frappe.throw(_("Invalid {0}.").format(what))
	if len(json.dumps(value, default=str)) > MAX_JSON:
		frappe.throw(_("The {0} is too large.").format(what))
	return value


def _load(text):
	try:
		data = json.loads(text or "{}")
	except ValueError:
		return {}
	return data if isinstance(data, dict) else {}


def _text(value, length=140):
	return "" if value is None else str(value).strip()[:length]


def _item_out(doc):
	data = _load(doc.data)
	data.update(id=doc.name, live=bool(doc.live), order=doc.sort_order or 0)
	return data


def _day(value):
	try:
		return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
	except (TypeError, ValueError):
		return None


def on_sale(data, now=None):
	"""True if a tour is inside its validFrom / validUntil window (Nairobi time, both days inclusive)."""
	now = now or datetime.now(TZ)
	start = _day(data.get("validFrom") or data.get("from"))
	end = _day(data.get("validUntil") or data.get("until"))
	if start and now < datetime.combine(start, time.min, TZ):
		return False
	if end and now > datetime.combine(end, time.max, TZ):
		return False
	return True


def _addons():
	try:
		value = json.loads(frappe.db.get_default(ADDONS_KEY) or "{}")
	except ValueError:
		value = {}
	return value if isinstance(value, dict) else {}


def _me():
	user = frappe.session.user
	admin = is_admin(user)
	return {
		"user": None if user == "Guest" else user,
		"full_name": frappe.utils.get_fullname(user) if admin else None,
		"is_admin": admin,
		"csrf_token": frappe.sessions.get_csrf_token() if admin else None,
	}


# ---------- public ----------
@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_catalog():
	"""Tours and vehicles. Visitors only get the ones marked as shown."""
	admin = is_admin()
	rows = frappe.get_all(
		ITEM,
		filters=None if admin else {"live": 1},
		fields=["name", "kind", "live", "sort_order", "data"],
		order_by="sort_order asc, creation asc",
		ignore_permissions=True,
	)
	out = {"tours": [], "vehicles": [], "packages": [], "me": _me(), "addons": _addons()}
	now = datetime.now(TZ)
	for row in rows:
		if row.kind in KINDS:
			item = _item_out(row)
			if row.kind in ("tours", "packages") and not admin and not on_sale(item, now):
				continue
			out[row.kind].append(item)
	return out


@frappe.whitelist(allow_guest=True, methods=["GET"])
def whoami():
	return _me()


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def submit_request(request):
	"""Save a booking or enquiry sent from the website."""
	req = _dict(request, "request")
	req = {_text(k, 60): v for k, v in req.items() if k not in ("owner", "status")}
	doc = frappe.get_doc(
		{
			"doctype": REQUEST,
			"status": "new",
			"kind": _text(req.get("kind"), 40),
			"item_title": _text(req.get("itemTitle")),
			"full_name": _text(req.get("name")),
			"phone": _text(req.get("phone"), 40),
			"email": _text(req.get("email")),
			"country": _text(req.get("country"), 80),
			"request_id": _text(req.get("id"), 40),
			"data": json.dumps(req, default=str),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def log_client_error(message, page=None):
	"""A JavaScript error from a visitor's browser, so website problems show up in Frappe's Error Log."""
	frappe.log_error(title="Website error", message=f"{_text(page, 300)}\n{_text(message, 500)}")
	return {"ok": True}


# ---------- admin ----------
@frappe.whitelist(methods=["GET"])
def get_requests():
	_require_admin()
	rows = frappe.get_all(
		REQUEST,
		fields=["name", "status", "data", "creation"],
		order_by="creation desc",
		limit_page_length=2000,
	)
	out = []
	for row in rows:
		r = _load(row.data)
		r.update(owner=row.name, status=row.status or "new")
		r.setdefault("id", row.name)
		r.setdefault("createdAt", row.creation.isoformat() if row.creation else "")
		out.append(r)
	return out


@frappe.whitelist(methods=["POST"])
def set_request_status(name, status):
	_require_admin()
	if status not in STATUSES:
		frappe.throw(_("Unknown status."))
	frappe.db.set_value(REQUEST, name, "status", status)
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def save_item(kind, data, name=None):
	"""Create (no name) or update (merge fields into) a tour or vehicle."""
	_require_admin()
	if kind not in KINDS:
		frappe.throw(_("Unknown kind."))
	changes = _dict(data)
	changes.pop("id", None)
	if name:
		doc = frappe.get_doc(ITEM, name)
		if doc.kind != kind:
			frappe.throw(_("Wrong kind."))
		merged = _load(doc.data)
	else:
		doc = frappe.new_doc(ITEM)
		doc.kind = kind
		merged = {}
	merged.update(changes)
	if "live" in merged:
		doc.live = 1 if merged.pop("live") not in (False, 0, None, "", "0") else 0
	if "order" in merged:
		try:
			doc.sort_order = float(merged.pop("order") or 0)
		except (TypeError, ValueError):
			doc.sort_order = 0
	doc.title = _text(merged.get("title") or merged.get("name") or merged.get("d"))
	doc.data = json.dumps(merged, default=str)
	if len(doc.data) > MAX_JSON:
		frappe.throw(_("This item is too large."))
	doc.save(ignore_permissions=True)
	if kind in ("tours", "packages") and frappe.conf.get("anthropic_api_key") and not changes.get("tr"):
		frappe.enqueue("pals_website.api.translate_item", name=doc.name, queue="short", enqueue_after_commit=True)
	return _item_out(doc)


@frappe.whitelist(methods=["POST"])
def save_addons(prices):
	"""Package add-on prices per person in KES. A null price shows "Price on request"."""
	_require_admin()
	prices = _dict(prices, "prices")
	clean = {}
	for key, value in list(prices.items())[:60]:
		key = _text(key, 80)
		if value in (None, ""):
			clean[key] = None
			continue
		try:
			clean[key] = max(0, round(float(value)))
		except (TypeError, ValueError):
			frappe.throw(_("Prices must be numbers."))
	frappe.db.set_default(ADDONS_KEY, json.dumps(clean))
	return {"ok": True, "prices": clean}


def _tour_strings(data):
	out = [data.get("title"), data.get("days"), data.get("region"), data.get("overview"), data.get("terms")]
	for key in ("highlights", "included", "excluded"):
		value = data.get(key) or []
		out += value.split("\n") if isinstance(value, str) else list(value)
	# holiday packages
	out += [data.get("d"), data.get("country"), data.get("about"), data.get("board"), data.get("tName")]
	for hotel in data.get("hotels") or []:
		if isinstance(hotel, dict):
			out.append(hotel.get("board"))
	for day in data.get("itinerary") or []:
		if isinstance(day, dict):
			out += [day.get("d"), day.get("title"), day.get("text")]
	seen, strings = set(), []
	for value in out:
		value = (value or "").strip() if isinstance(value, str) else ""
		if value and value not in seen:
			seen.add(value)
			strings.append(value)
	return strings[:120]


def translate_item(name):
	"""Background job: translate a tour's text into the website's other languages with Claude."""
	import requests

	key = frappe.conf.get("anthropic_api_key")
	if not key:
		return
	doc = frappe.get_doc(ITEM, name)
	data = _load(doc.data)
	strings = _tour_strings(data)
	if not strings:
		return
	prompt = (
		"You translate website text for Pals Travel & Leisure, a safari and travel company in Nairobi, Kenya. "
		"Translate each English string into " + ", ".join(f"{v} ({k})" for k, v in LANGS.items()) + ". "
		"Keep place names, hotel names, prices and numbers as they are. Use warm, natural, plain wording that a native speaker would write. "
		"Reply with JSON only, in the form {\"sw\": {\"<english>\": \"<translation>\"}, \"fr\": {...}, ...}, using every language code above.\n\n"
		+ json.dumps(strings, ensure_ascii=False)
	)
	resp = requests.post(
		"https://api.anthropic.com/v1/messages",
		headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
		json={"model": frappe.conf.get("anthropic_model") or "claude-haiku-5-5", "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}]},
		timeout=180,
	)
	resp.raise_for_status()
	text = "".join(part.get("text", "") for part in resp.json().get("content", []) if part.get("type") == "text")
	text = text[text.find("{"): text.rfind("}") + 1]
	result = json.loads(text)
	tr = {}
	for code in LANGS:
		block = result.get(code) or {}
		tr[code] = {k: str(v) for k, v in block.items() if k in strings and isinstance(v, (str, int, float))}
	data = _load(frappe.db.get_value(ITEM, name, "data"))  # re-read in case the admin edited meanwhile
	data["tr"] = tr
	frappe.db.set_value(ITEM, name, "data", json.dumps(data, default=str, ensure_ascii=False))
	frappe.db.commit()


@frappe.whitelist(methods=["POST"])
def delete_item(name):
	_require_admin()
	frappe.delete_doc(ITEM, name, ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def import_items(tours=None, vehicles=None):
	"""First-time setup: copy data/tours.json and data/vehicles.json into Frappe.
	A kind is only imported while it has no items yet."""
	_require_admin()
	done = {}
	for kind, items in (("tours", tours), ("vehicles", vehicles)):
		if isinstance(items, str):
			items = json.loads(items or "[]")
		if not isinstance(items, list) or frappe.db.count(ITEM, {"kind": kind}):
			done[kind] = 0
			continue
		for item in items[:500]:
			if isinstance(item, dict):
				save_item(kind, item)
		done[kind] = len(items[:500])
	return done


@frappe.whitelist(methods=["POST"])
def upload_image():
	"""Upload a photo for a tour or vehicle. Returns its public URL."""
	_require_admin()
	upload = frappe.request.files.get("file") if frappe.request else None
	if not upload:
		frappe.throw(_("No file received."))
	filename = os.path.basename(upload.filename or "photo.jpg")
	if os.path.splitext(filename)[1].lower() not in IMAGE_TYPES:
		frappe.throw(_("Please upload a JPG, PNG, WebP or GIF image."))
	content = upload.stream.read(MAX_IMAGE + 1)
	if len(content) > MAX_IMAGE:
		frappe.throw(_("Images must be 10 MB or smaller."))
	file = frappe.get_doc({"doctype": "File", "file_name": filename, "content": content, "is_private": 0})
	file.save(ignore_permissions=True)
	return {"url": frappe.utils.get_url(file.file_url)}
