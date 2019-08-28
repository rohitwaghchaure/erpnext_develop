# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import json, io
import pyqrcode
from six import string_types
from frappe.utils import now, get_datetime_str
from erpnext.regional.italy.utils import get_company_country
from requests_pkcs12 import get, post
from erpnext.controllers.sales_and_purchase_return import make_return_doc

def sales_invoice_on_submit(doc, method):
	if get_company_country(doc.company) not in ["Fiji"]:
		return

	validate_vsdc_invoice(doc)

def validate_vsdc_invoice(doc):
	if not(doc.is_pos and doc.pos_profile): return

	branch = frappe.db.get_value("POS Profile", doc.pos_profile, "location")
	branch_data = frappe.db.get_value("Branch", branch, 
		["attach_certificate as path", "password", "pac", "tin", "name"], as_dict=1)

	args = prepare_args_for_request(doc, branch_data)

	sdc_settings_doc = frappe.get_doc("SDC Settings", "SDC Settings")

	file_name = frappe.db.get_value("File", {'file_url': branch_data.path}, "name")
	_file_doc = frappe.get_doc("File", file_name)

	response = post(sdc_settings_doc.vsdc_url, data=json.dumps(args), 
    	headers={'Content-Type': 'application/json'}, 
    	verify=False,
    	pkcs12_filename=_file_doc.get_full_path(), pkcs12_password=branch_data.get("password"))

	dict_response = json.loads(response.text)

	if response and response.status_code == 200:
		doc.update({
			'verification_url': get_qrcode(dict_response.get("VerificationUrl")),
			'company_tin': dict_response.get("TIN"),
			'tax_items': json.dumps(dict_response.get("TaxItems")),
			'fiscal_address': dict_response.get("Address"),
			'district': dict_response.get("District"),
			'sdc_time': get_datetime_str(dict_response.get("DT")),
			'sdc_invoice_no': dict_response.get("IN"),
			'invoice_counter': dict_response.get("IC"),
			'business_name': dict_response.get("BusinessName")
		})

		if doc.inv_ref_no:
			doc.db_set("inv_ref_no", doc.inv_ref_no)

	create_sdc_log(doc, args, dict_response, response)
	return doc

def prepare_args_for_request(doc, branch_data):
	items = []

	taxes = []
	if doc.taxes:
		taxes = [d.get("account_head") for d in doc.taxes]

	for d in doc.items:
		args = {
			"Name": d.item_name,
			"Quantity": abs(d.qty),
			"UnitPrice": d.rate,
			"Discount": abs(d.discount_amount),
			"TotalAmount": abs(d.amount)
		}

		labels = []
		if d.gtin:
			args["GTIN"] = d.gtin
		
		if d.item_tax_rate and taxes:
			item_tax_dict = json.loads(d.item_tax_rate)
			for account_head in item_tax_dict:
				if account_head in taxes:
					label = frappe.db.get_value("Account", account_head, "tax_label")
					d.tax_label = label
					labels.append(label)

		if labels:
			args["Labels"] = labels

		items.append(args)

	invoice_args = {
		"DateAndTimeOfIssue": get_datetime_str(doc.creation),
		"Cashier": doc.cashier_tin,
		"BD": "",
		"BuyerCostCenterId": "",
		"IT": doc.fiji_invoice_type,
		"TT": doc.fiji_transaction_type,
		"PaymentType": "Cash",
		"InvoiceNumber": doc.return_against if doc.is_return else doc.name,
		"PAC": branch_data.get("pac"),
		"Options":{
			"OmitQRCodeGen": "1",
			"OmitTextualRepresentation": "0"
		},
		"Items": items
	}

	if branch_data.get("name"):
		invoice_args["TIN"] = branch_data.get("tin")
		invoice_args["LocationName"] = branch_data.get("name")

	if doc.is_return or doc.fiji_invoice_type == 'Copy':
		invoice_args["ReferentDocumentNumber"] = doc.sdc_invoice_no

	return invoice_args

def create_sdc_log(doc, requsted_data, dict_response, response):
	frappe.get_doc({
		"doctype": "SDC Log",
		"docname": doc.name,
		"requested_data": json.dumps(requsted_data),
		"response": response.text,
		"verification_url": dict_response.get("VerificationUrl")
	}).insert()

def get_qrcode(value):
	url = pyqrcode.create(value)
	url.svg('uca.svg', scale=100) 
	buffer = io.BytesIO()
	url.svg(buffer)

	svg_data = buffer.getvalue()
	# svg_data = svg_data.replace('class="pyqrcode"', 'class="pyqrcode" data-qrcode-value= "%s"' % value)

	return svg_data

@frappe.whitelist()
def get_sdc_invoice_details(invoice_type, transaction_type, sdc_invoice_no):
	name = frappe.get_cached_value("Sales Invoice",
		{'sdc_invoice_no': sdc_invoice_no}, 'name')

	if not name:
		frappe.throw(_("The SDC invoice number {0} does not exist").format(sdc_invoice_no))

	if transaction_type == "Refund":
		new_doc = make_return_doc("Sales Invoice", name)
		new_doc.verification_url = invoice_type
		new_doc.inv_ref_no = sdc_invoice_no
	else:
		new_doc = frappe.get_doc("Sales Invoice", name)

	new_doc.fiji_transaction_type = transaction_type
	new_doc.fiji_invoice_type = invoice_type

	return new_doc.as_dict()

@frappe.whitelist()
def copy_invoice(invoice_type, transaction_type, name, ref_no):
	if invoice_type != 'Copy':
		frappe.throw(_("Invoice type should be copy"))

	doc = frappe.get_doc("Sales Invoice", name)
	doc.update({
		"fiji_invoice_type": invoice_type,
		"fiji_transaction_type": transaction_type,
		"inv_ref_no": ref_no
	})

	return validate_vsdc_invoice(doc)

@frappe.whitelist()
def submit_sales_return_entry(doc):
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	s_doc = frappe.get_doc(doc)
	s_doc.status = 'Return'
	s_doc.submit()

	return s_doc.as_dict()