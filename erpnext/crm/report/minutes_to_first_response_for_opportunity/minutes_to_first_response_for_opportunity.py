# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import build_match_conditions

def execute(filters=None):
	match_conditions = build_match_conditions("Opportunity")
	cond = ""
	if match_conditions:
		cond = "and {0}".format(match_conditions)

	columns = [
		{
			'fieldname': 'creation_date',
			'label': 'Date',
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'mins',
			'fieldtype': 'Float',
			'label': 'Mins to First Response'
		},
	]

	data = frappe.db.sql('''select date(creation) as creation_date,
		avg(mins_to_first_response) as mins
		from tabOpportunity
			where date(creation) between %s and %s
			and mins_to_first_response > 0 {match_cond}
		group by creation_date order by creation_date desc'''.format(match_cond = cond),
		(filters.from_date, filters.to_date), debug=1)

	return columns, data
