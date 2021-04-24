# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
from erpnext.stock.stock_ledger import get_stock_ledger_entries
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [{
		'label': _('Posting Date'),
		'fieldtype': 'Date',
		'fieldname': 'posting_date'
	}, {
		'label': _('Voucher Type'),
		'fieldtype': 'Link',
		'fieldname': 'voucher_type',
		'options': 'DocType'
	}, {
		'label': _('Voucher No'),
		'fieldtype': 'Dynamic Link',
		'fieldname': 'voucher_no',
		'options': 'voucher_type'
	}, {
		'label': _('Company'),
		'fieldtype': 'Link',
		'fieldname': 'company',
		'options': 'Company'
	}, {
		'label': _('Warehouse'),
		'fieldtype': 'Link',
		'fieldname': 'warehouse',
		'options': 'Warehouse'
	}, {
		'label': _('Serial No'),
		'fieldtype': 'Link',
		'fieldname': 'serial_no',
		'options': 'Serial No'
	}, {
		'label': _('In Qty'),
		'fieldtype': 'Float',
		'fieldname': 'in_qty'
	}, {
		'label': _('Out Qty'),
		'fieldtype': 'Float',
		'fieldname': 'out_qty'
	}, {
		'label': _('Balance Qty'),
		'fieldtype': 'Float',
		'fieldname': 'balance_qty'
	}, {
		'label': _('Incoming Rate'),
		'fieldtype': 'Currency',
		'fieldname': 'incoming_rate'
	}, {
		'label': _('Valuation Rate'),
		'fieldtype': 'Currency',
		'fieldname': 'valuation_rate'
	}, {
		'label': _('Balance Value'),
		'fieldtype': 'Currency',
		'fieldname': 'stock_value'
	}]

	if not filters.get('serial_no'):
		columns.append({
			'label': _('Available Serial No'),
			'fieldtype': 'Data',
			'fieldname': 'available_serial_nos',
			'width': 350
		})

	return columns

def get_data(filters):
	data = get_stock_ledger_entries(filters, '<=', order="asc")

	prev_row_bal_qty = {}
	available_serial_nos = {}
	for row in data:
		if row.warehouse not in prev_row_bal_qty:
			prev_row_bal_qty.setdefault(row.warehouse, 0)

		if row.warehouse not in available_serial_nos:
			available_serial_nos.setdefault(row.warehouse, [])

		prev_row_qty = prev_row_bal_qty[row.warehouse]
		available_sns = available_serial_nos[row.warehouse]

		if not row.balance_qty:
			row.balance_qty = 0.0

		if row.actual_qty > 0:
			row.in_qty = row.actual_qty
		else:
			row.out_qty = row.actual_qty

		row.balance_qty = prev_row_qty + row.actual_qty
		prev_row_bal_qty[row.warehouse] = row.balance_qty

		serial_nos = get_serial_nos(row.serial_no)
		if row.actual_qty > 0:
			available_sns.extend(serial_nos)
		elif row.actual_qty < 0:
			for sn in serial_nos:
				if sn in available_sns:
					available_sns.remove(sn)

		row.available_serial_nos = ','.join(available_sns)

	return data

