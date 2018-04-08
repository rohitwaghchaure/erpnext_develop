# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import build_match_conditions
from frappe import _

@frappe.whitelist()
def get_funnel_data(from_date, to_date, user=None):
	match_conditions = build_match_conditions("Lead")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)

	if user:
		cond += " and owner = '{0}'".format(user)

	active_leads = frappe.db.sql("""select count(*) from `tabLead`
		where (date(`modified`) between %s and %s)
		and status != "Do Not Contact" {0} """.format(cond), (from_date, to_date))[0][0]

	match_conditions = build_match_conditions("Customer")
	cond = "1=1"
	if match_conditions:
		cond = "{0}".format(match_conditions)
	if user:
		cond += " and owner = '{0}'".format(user)

	active_leads += frappe.db.sql("""select count(distinct contact.name) from `tabContact` contact
		left join `tabDynamic Link` dl on (dl.parent=contact.name) where dl.link_doctype='Customer' 
		and (date(contact.modified) between %s and %s) and status != "Passive" and 
		dl.link_name in (select name from `tabCustomer` where {0}) """.format(cond), (from_date, to_date))[0][0]

	match_conditions = build_match_conditions("Opportunity")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if user:
		cond += " and owner = '{0}'".format(user)

	opportunities = frappe.db.sql("""select count(*) from `tabOpportunity`
		where (date(`creation`) between %s and %s)
		and status != "Lost" {0}""".format(cond), (from_date, to_date))[0][0]

	match_conditions = build_match_conditions("Quotation")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if user:
		cond += " and owner = '{0}'".format(user)

	quotations = frappe.db.sql("""select count(*) from `tabQuotation`
		where docstatus = 1 and (date(`creation`) between %s and %s)
		and status != "Lost" {0}""".format(cond), (from_date, to_date))[0][0]

	match_conditions = build_match_conditions("Sales Order")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if user:
		cond += " and owner = '{0}'".format(user)

	sales_orders = frappe.db.sql("""select count(*) from `tabSales Order`
		where docstatus = 1 and (date(`creation`) between %s and %s) {0}
		""".format(cond), (from_date, to_date))[0][0]

	return [
		{ "title": _("Active Leads / Customers"), "value": active_leads, "color": "#B03B46" },
		{ "title": _("Opportunities"), "value": opportunities, "color": "#F09C00" },
		{ "title": _("Quotations"), "value": quotations, "color": "#006685" },
		{ "title": _("Sales Orders"), "value": sales_orders, "color": "#00AD65" }
	]

def get_users(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select distinct parent from `tabHas Role` where parenttype = 'User'
		and role in ('Sales Master Head', 'System Manager', 'Administrator') and
		parent like '{txt}' order by parent limit {start}, {page_len}
		""".format(txt=frappe.db.escape('%{0}%'.format(txt)),start=start,page_len=page_len))