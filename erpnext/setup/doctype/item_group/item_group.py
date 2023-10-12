# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import copy

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet
from frappe.website.utils import clear_cache


class ItemGroup(NestedSet):
	def validate(self):
		if not self.parent_item_group and not frappe.flags.in_test:
			if frappe.db.exists("Item Group", _("All Item Groups")):
				self.parent_item_group = _("All Item Groups")
		self.validate_item_group_defaults()
		self.check_item_tax()

	def check_item_tax(self):
		"""Check whether Tax Rate is not entered twice for same Tax Type"""
		check_list = []
		for d in self.get("taxes"):
			if d.item_tax_template:
				if (d.item_tax_template, d.tax_category) in check_list:
					frappe.throw(
						_("{0} entered twice {1} in Item Taxes").format(
							frappe.bold(d.item_tax_template),
							"for tax category {0}".format(frappe.bold(d.tax_category)) if d.tax_category else "",
						)
					)
				else:
					check_list.append((d.item_tax_template, d.tax_category))

	def on_update(self):
		NestedSet.on_update(self)
		invalidate_cache_for(self)
		self.validate_one_root()
		self.delete_child_item_groups_key()

	def on_trash(self):
		NestedSet.on_trash(self, allow_root_deletion=True)
		self.delete_child_item_groups_key()

	def delete_child_item_groups_key(self):
		frappe.cache().hdel("child_item_groups", self.name)

	def validate_item_group_defaults(self):
		from erpnext.stock.doctype.item.item import validate_item_default_company_links

		validate_item_default_company_links(self.item_group_defaults)


def get_child_groups_for_website(item_group_name, immediate=False, include_self=False):
	"""Returns child item groups *excluding* passed group."""
	item_group = frappe.get_cached_value("Item Group", item_group_name, ["lft", "rgt"], as_dict=1)
	filters = {"lft": [">", item_group.lft], "rgt": ["<", item_group.rgt], "show_in_website": 1}

	if immediate:
		filters["parent_item_group"] = item_group_name

	if include_self:
		filters.update({"lft": [">=", item_group.lft], "rgt": ["<=", item_group.rgt]})

	return frappe.get_all("Item Group", filters=filters, fields=["name", "route"], order_by="name")


def get_child_item_groups(item_group_name):
	item_group = frappe.get_cached_value("Item Group", item_group_name, ["lft", "rgt"], as_dict=1)

	child_item_groups = [
		d.name
		for d in frappe.get_all(
			"Item Group", filters={"lft": (">=", item_group.lft), "rgt": ("<=", item_group.rgt)}
		)
	]

	return child_item_groups or {}


def get_parent_item_groups(item_group_name, from_item=False):
	base_nav_page = {"name": _("All Products"), "route": "/all-products"}

	if from_item and frappe.request.environ.get("HTTP_REFERER"):
		# base page after 'Home' will vary on Item page
		last_page = frappe.request.environ["HTTP_REFERER"].split("/")[-1].split("?")[0]
		if last_page and last_page in ("shop-by-category", "all-products"):
			base_nav_page_title = " ".join(last_page.split("-")).title()
			base_nav_page = {"name": _(base_nav_page_title), "route": "/" + last_page}

	base_parents = [
		{"name": _("Home"), "route": "/"},
		base_nav_page,
	]

	if not item_group_name:
		return base_parents

	item_group = frappe.db.get_value("Item Group", item_group_name, ["lft", "rgt"], as_dict=1)
	parent_groups = frappe.db.sql(
		"""select name, route from `tabItem Group`
		where lft <= %s and rgt >= %s
		and show_in_website=1
		order by lft asc""",
		(item_group.lft, item_group.rgt),
		as_dict=True,
	)

	return base_parents + parent_groups


def invalidate_cache_for(doc, item_group=None):
	if not item_group:
		item_group = doc.name

	for d in get_parent_item_groups(item_group):
		item_group_name = frappe.db.get_value("Item Group", d.get("name"))
		if item_group_name:
			clear_cache(frappe.db.get_value("Item Group", item_group_name, "route"))


def get_item_group_defaults(item, company):
	item = frappe.get_cached_doc("Item", item)
	item_group = frappe.get_cached_doc("Item Group", item.item_group)

	for d in item_group.item_group_defaults or []:
		if d.company == company:
			row = copy.deepcopy(d.as_dict())
			row.pop("name")
			return row

	return frappe._dict()
