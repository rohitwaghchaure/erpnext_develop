frappe.ui.form.on("Sales Invoice", {
	setup: function(frm) {
        debugger
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
	}
});