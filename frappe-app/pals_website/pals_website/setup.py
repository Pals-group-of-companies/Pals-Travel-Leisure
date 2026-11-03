import frappe

ROLE = "Pals Website Manager"


def ensure_role():
	"""Create the role that may use the website admin dashboard."""
	if not frappe.db.exists("Role", ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": ROLE, "desk_access": 0}).insert(ignore_permissions=True)
		frappe.db.commit()
