# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.permissions import add_permission, update_permission_property
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def setup(company=None, patch=True):
	make_custom_fields()
	create_property_setters()
	add_permissions()

def make_custom_fields(update=True):
	custom_fields = {
		'Branch': [
			dict(fieldname='certificate_info', label='Certificate Info', fieldtype='Section Break',
				insert_after='posting_date'),
			dict(fieldname='attach_certificate', label='Attach Certificate', fieldtype='Attach',
				insert_after='certificate_info'),
			dict(fieldname='qr_code_details', label='', fieldtype='Column Break',
				insert_after='attach_certificate'),
			dict(fieldname='password', label='Password',
				fieldtype='Data', insert_after='attach_certificate', reqd=1),
			dict(fieldname='pac', label='PAC',
				fieldtype='Data', insert_after='password', reqd=1),
			dict(fieldname='tin', label='TIN',
				fieldtype='Data', insert_after='pac'),
		],
		'Sales Invoice': [
			dict(fieldname='fiscal_invoice', label='Fiscal Invoice Info', fieldtype='Section Break',
				insert_after='cost_center', depends_on='is_pos'),
			dict(fieldname='fiji_invoice_type', label='Invoice Type', fieldtype='Select',
				insert_after='fiscal_invoice', options='\nNormal\nCopy', default='Normal'),
			dict(fieldname='fiji_transaction_type', label='Transaction Type', fieldtype='Select',
				insert_after='fiji_invoice_type', options='\nRefund\nSale', default='Sale'),
			dict(fieldname='cashier_tin', label='Cashier TIN', fieldtype='Data',
				insert_after='fiji_transaction_type', fetch_from = 'owner.cashier_tin'),
			dict(fieldname='company_tin', label='TIN', fieldtype='Data',
				insert_after='cashier_tin', read_only=1),
			dict(fieldname='tax_items', label='Tax Items', fieldtype='Code',
				insert_after='company_tin', read_only=1),
			dict(fieldname='fiscal_address', label='Fiscal Address', fieldtype='Data',
				insert_after='tax_items', read_only=1),
			dict(fieldname='district', label='District', fieldtype='Data',
				insert_after='fiscal_address', read_only=1),
			dict(fieldname='inv_ref_no', label='Ref No', fieldtype='Data',
				insert_after='district', read_only=1),
			dict(fieldname='qr_code_details', label='', fieldtype='Column Break',
				insert_after='tax_details'),
			dict(fieldname='business_name', label='Business Name', fieldtype='Data',
				insert_after='qr_code_details', read_only=1),
			dict(fieldname='sdc_time', label='SDC Time', fieldtype='Data',
				insert_after='verification_url', read_only=1),
			dict(fieldname='sdc_invoice_no', label='SDC Invoice No', fieldtype='Data',
				insert_after='sdc_time', read_only=1),
			dict(fieldname='invoice_counter', label='Invoice Counter', fieldtype='Data',
				insert_after='sdc_invoice_no', read_only=1),
			dict(fieldname='verification_url', label='Verification URL', fieldtype='Qrcode',
				insert_after='invoice_counter', read_only=1),
			dict(fieldname='buyer_cost_center', label='Buyer Cost Center',
				fieldtype='Data', insert_after='tax_id', read_only=1, fetch_from="customer.buyer_cost_center")
		],
		'Sales Invoice Item': [
			dict(fieldname='gtin', label='GTIN', fieldtype='Data',
				insert_after='description', read_only=1, fetch_from="item_code.gtin"),
			dict(fieldname='tax_label', label='Tax Label', fieldtype='Data',
				insert_after='gtin', read_only=1)
		],
		'Item': [
			dict(fieldname='gtin', label='GTIN',
				fieldtype='Data', insert_after='item_group')
		],
		'POS Profile': [
			dict(fieldname='certificate_info', label='SDC Settings', fieldtype='Section Break',
				insert_after='cost_center'),
			dict(fieldname='location', label='Location',
				fieldtype='Link', options='Branch', insert_after='certificate_info')
		],
		'User': [
			dict(fieldname='cashier_tin', label='Cashier TIN',
				fieldtype='Data', insert_after='time_zone'),
		],
		'Account': [
			dict(fieldname='tax_label', label='Tax Label', depends_on="eval:doc.account_type=='Tax'",
				fieldtype='Select', options='\nA\nB\nC\nE\nF\nP\nN', insert_after='tax_rate')
		],
		'Customer': [
			dict(fieldname='buyer_cost_center', label='Buyer Cost Center',
				fieldtype='Data', insert_after='tax_id')
		]
	}
	create_custom_fields(custom_fields, update=update)

def create_property_setters():
	make_property_setter("Customer", 'tax_id', 'label', 'Buyer TIN', 'Data')
	make_property_setter("Sales Invoice", 'tax_id', 'label', 'Buyer TIN', 'Data')

def add_permissions():
	add_permission("SDC Settings", 'Accounts Manager', 0)
	add_permission("SDC Settings", 'Accounts User', 0)
	update_permission_property("SDC Settings", 'Accounts Manager', 0, 'write', 1)
	update_permission_property("SDC Settings", 'Accounts Manager', 0, 'create', 1)
	update_permission_property("SDC Settings", 'Accounts User', 0, 'write', 1)
	update_permission_property("SDC Settings", 'Accounts User', 0, 'create', 1)