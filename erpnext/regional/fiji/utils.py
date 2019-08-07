# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import json, io
import pyqrcode
from frappe.utils import now, get_datetime_str
from erpnext.regional.italy.utils import get_company_country
from requests_pkcs12 import get, post

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
		verification_url = get_qrcode(dict_response.get("VerificationUrl"))
		doc.db_set("verification_url", verification_url)
		doc.db_set("company_tin", dict_response.get("TIN"))
		doc.db_set("tax_items", json.dumps(dict_response.get("TaxItems")))
		doc.db_set("fiscal_address", dict_response.get("Address"))
		doc.db_set("district", dict_response.get("District"))
		doc.db_set("sdc_time", get_datetime_str(dict_response.get("DT")))
		doc.db_set("sdc_invoice_no", dict_response.get("IN"))
		doc.db_set("invoice_counter", dict_response.get("IC"))

	create_sdc_log(doc, args, dict_response, response)

def prepare_args_for_request(doc, branch_data):
	items = []

	taxes = []
	if doc.taxes:
		taxes = [d.account_head for d in doc.taxes]

	for d in doc.items:
		args = {
			"Name": d.item_name,
			"Quantity": d.qty,
			"UnitPrice": d.rate,
			"Discount": d.discount_amount,
			"TotalAmount": d.amount
		}

		labels = []
		if d.gtin:
			args["GTIN"] = d.gtin
		
		if d.item_tax_rate and taxes:
			item_tax_dict = json.loads(d.item_tax_rate)
			for account_head in item_tax_dict:
				if account_head in taxes:
					labels.append(frappe.db.get_value("Account", account_head, "tax_label"))

		if labels:
			args["Labels"] = labels

		items.append(args)

	invoice_args = {
		"DateAndTimeOfIssue": doc.creation,
		"Cashier": doc.cashier_tin,
		"BD": "",
		"BuyerCostCenterId": "",
		"IT": "Normal",
		"TT": "Sale",
		"PaymentType": "Cash",
		"InvoiceNumber": doc.name,
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
	svg_data = svg_data.replace('class="pyqrcode"', 'class="pyqrcode" data-qrcode-value= "%s"' % value)

	return svg_data
