// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Workstation Operating Component", {
	refresh(frm) {
		frm.set_query("expense_account", "accounts", (doc, cdt, cdn) => {
			const d = locals[cdt][cdn];
			return {
				filters: { company: doc.company, root_type: "Expense", is_group: 0 },
			};
		});
	},
});
