# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns() or []
	data = get_data() or []

	return columns, data

def get_columns():
	return [
		{
			"label": _("Lead Id"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Lead",
			"width": 90
		},
		{
			"label": _("Lead Name"),
			"fieldname": "lead_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Address"),
			"fieldname": "address",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("State"),
			"fieldname": "state",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Pincode"),
			"fieldname": "pincode",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Country"),
			"fieldname": "country",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Phone"),
			"fieldname": "phone",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Mobile No"),
			"fieldname": "mobile_no",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Email Id"),
			"fieldname": "email_id",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Lead Owner"),
			"fieldname": "lead_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 100
		},
		{
			"label": _("Source"),
			"fieldname": "source",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Territory"),
			"fieldname": "territory",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Owner"),
			"fieldname": "owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 100
		}
	]

def get_data():
	from frappe.desk.reportview import build_match_conditions
	
	match_conditions = build_match_conditions("Lead")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)

	return frappe.db.sql("""
		SELECT
		    `tabLead`.name, `tabLead`.lead_name, `tabLead`.company_name, `tabLead`.status,
			concat_ws(', ',
				trim(',' from `tabAddress`.address_line1),
				trim(',' from tabAddress.address_line2)
			) as address,
			`tabAddress`.state,`tabAddress`.pincode, `tabAddress`.country,`tabLead`.phone, `tabLead`.mobile_no,
			`tabLead`.email_id, `tabLead`.lead_owner, `tabLead`.source, `tabLead`.territory, `tabLead`.owner
		FROM
			`tabLead`
			left join `tabDynamic Link` on (
				`tabDynamic Link`.link_name=`tabLead`.name
			)
			left join `tabAddress` on (
				`tabAddress`.name=`tabDynamic Link`.parent
			)
		WHERE
			`tabLead`.docstatus < 2 {0}
		ORDER BY
			`tabLead`.name asc
	""".format(cond))