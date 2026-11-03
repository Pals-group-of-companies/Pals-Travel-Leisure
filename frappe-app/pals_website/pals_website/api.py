"""API used by the Pals Travel & Leisure website (index.html).

Public (no login):
  get_catalog      tours and vehicles shown on the website
  submit_request   a visitor's booking / enquiry form

Website admins only (role "Pals Website Manager" or "System Manager"):
  get_requests, set_request_status, save_item, delete_item,
  import_items, upload_image

Admins sign in with Frappe's own /api/method/login, so passwords are checked
and stored (hashed) by Frappe, and failed attempts are throttled by Frappe.
"""

import json
import os

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

ROLE = "Pals Website Manager"
ITEM = "Pals Website Item"
REQUEST = "Pals Booking Request"
KINDS = ("tours", "vehicles")
STATUSES = ("new", "contacted", "confirmed", "cancelled")
MAX_JSON = 60_000  # characters
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
	out = {"tours": [], "vehicles": [], "me": _me()}
	for row in rows:
		if row.kind in KINDS:
			out[row.kind].append(_item_out(row))
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
	doc.title = _text(merged.get("title") or merged.get("name"))
	doc.data = json.dumps(merged, default=str)
	if len(doc.data) > MAX_JSON:
		frappe.throw(_("This item is too large."))
	doc.save(ignore_permissions=True)
	return _item_out(doc)


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
