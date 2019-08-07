from __future__ import unicode_literals
import frappe
from erpnext.regional.fiji.setup import setup

def execute():
	frappe.reload_doc("core", "doctype", "docfield")
	frappe.reload_doc("custom", "doctype", "custom_field")
	frappe.reload_doc("custom", "doctype", "customize_form_field")

	company = frappe.get_all("Company", filters = {"country": "Fiji"})
	if not company:
		return

	setup()