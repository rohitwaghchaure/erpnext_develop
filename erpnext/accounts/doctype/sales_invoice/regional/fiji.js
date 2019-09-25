frappe.ui.form.on("Sales Invoice", {
	setup: function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				filters: {"name": user},
				fieldname: "cashier_tin"
			},
			callback: function(r){
				if(r.message){
					frm.set_value("cashier_tin", r.message.cashier_tin);
				}
			}
		});
	},

	refresh: function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "SDC Settings",
				fieldname: "vsdc_url"
			},
			callback: function(r){
				if(r.message && !r.message.vsdc_url){
					setTimeout(() => frappe.set_route('Form', 'SDC Settings', 'SDC Settings'), 2000);
					frappe.throw(__("VSDC url is required to use point of sale."));
				}
			}
		});
	}
});