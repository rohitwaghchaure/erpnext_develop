# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from frappe.desk.reportview import build_match_conditions
from frappe import _

@frappe.whitelist()
def get_funnel_data(from_date, to_date, user=None, all_user=0):
	if cint(all_user) and not user:
		user = get_users_list()
		users = [d[0] for d in user]
	elif not user:
		users = [frappe.session.user]
	else:
		users = [user]

	match_conditions = build_match_conditions("Lead")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)

	if users:
		owner_cond = " and owner in %s".format(','.join(['%s'] * len(users)))

	active_leads = frappe.db.sql("""select count(*) from `tabLead`
		where (date(`modified`) between %s and %s)
		and status != "Do Not Contact" {0} {1} """.format(cond, owner_cond), (from_date, to_date, tuple(users)))[0][0]

	match_conditions = build_match_conditions("Customer")
	cond = "1=1"
	if match_conditions:
		cond = "{0}".format(match_conditions)
	if users:
		owner_cond = " and owner in %s".format(','.join(['%s'] * len(users)))

	active_leads += frappe.db.sql("""select count(distinct contact.name) from `tabContact` contact
		left join `tabDynamic Link` dl on (dl.parent=contact.name) where dl.link_doctype='Customer' 
		and (date(contact.modified) between %s and %s) and status != "Passive" and 
		dl.link_name in (select name from `tabCustomer` where {0} {1}) """.format(cond, owner_cond),
		(from_date, to_date, tuple(users)))[0][0]

	match_conditions = build_match_conditions("Opportunity")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if users:
		owner_cond = " and owner in %s".format(','.join(['%s'] * len(users)))

	opportunities = frappe.db.sql("""select count(*) from `tabOpportunity`
		where (date(`creation`) between %s and %s)
		and status != "Lost" {0} {1}""".format(cond, owner_cond), (from_date, to_date, tuple(users)))[0][0]

	match_conditions = build_match_conditions("Quotation")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if users:
		owner_cond = " and owner in %s".format(','.join(['%s'] * len(users)))

	quotations = frappe.db.sql("""select count(*) from `tabQuotation`
		where docstatus = 1 and (date(`creation`) between %s and %s)
		and status != "Lost" {0} {1}""".format(cond, owner_cond), (from_date, to_date, tuple(users)))[0][0]

	match_conditions = build_match_conditions("Sales Order")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)
	if users:
		owner_cond = " and owner in %s".format(','.join(['%s'] * len(users)))

	sales_orders = frappe.db.sql("""select count(*) from `tabSales Order`
		where docstatus = 1 and (date(`creation`) between %s and %s) {0} {1}
		""".format(cond, owner_cond), (from_date, to_date, tuple(users)))[0][0]

	return [
		{ "title": _("Active Leads / Customers"), "value": active_leads, "color": "#B03B46" },
		{ "title": _("Opportunities"), "value": opportunities, "color": "#F09C00" },
		{ "title": _("Quotations"), "value": quotations, "color": "#006685" },
		{ "title": _("Sales Orders"), "value": sales_orders, "color": "#00AD65" }
	]

def get_users(doctype, txt, searchfield, start, page_len, filters):
	return get_users_list(txt, start, page_len)

def get_users_list(txt='', start=0, page_len=20):
	roles = {
		'Administrator': ['Sales Master Manager', 'Sales Manager'],
		'System Manager': ['Sales Master Manager', 'Sales Manager'],
		'Sales Master Manager': ['Sales Manager']
	}

	user_roles = get_user_roles(frappe.session.user)

	allowed_roles = []
	for d in roles:
		if d in user_roles:
			allowed_roles = roles[d]

	users =  frappe.db.sql(""" select distinct parent from `tabHas Role` where parenttype = 'User'
		and role in ({roles}) and
		parent like '{txt}' order by parent limit {start}, {page_len}
		""".format(roles = ','.join(['%s'] * len(allowed_roles)),
		txt=frappe.db.escape('%{0}%'.format(txt)),start=start,page_len=page_len), tuple(allowed_roles), as_list=1)

	allowed_users = []
	for d in users:
		if not set(get_user_roles(d[0])).intersection(set(['System Manager', 'Sales Master Manager'])):
			allowed_users.append(d)

	return allowed_users

def get_user_roles(user):
	return frappe.db.sql_list(""" select role from `tabHas Role`
		where parent = %s and parenttype = 'User'""", user)