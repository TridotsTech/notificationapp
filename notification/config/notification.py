from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label":_("Alerts"),
			"icon":_("fa fa-home"),
			"items":[
				{
					"type": "doctype",
					"name": "App Alert"
				},
				{
					"type": "doctype",
					"name": "SMS Alert"
				},
				{
					"type": "doctype",
					"name": "Email Alert"
				}
			]
		},
		{
			"label": _("Bulk Notification"),
			"icon":_("fa-user-plus"),
			"items": [
				{
					"type": "doctype",
					"name": "Notification Center"
				},
				{
					"type": "doctype",
					"name": "SMS Center"
				}
			]
		},
		{
			"label": _("History"),
			"icon":_("fa-user-plus"),
			"items": [
				{
					"type": "doctype",
					"name": "Notification History"
				}
				
			]
		},
		{
			"label": _("Queue"),
			"icon":_("fa-user-plus"),
			"items": [
				{
					"type": "doctype",
					"name": "Notification Queue"
				}
				
			]
		},
		{
			"label": _("Settings"),
			"icon":_("fa-user-plus"),
			"items": [
				{
					"type": "doctype",
					"name": "App Alert Settings"
				},
				{
					"type": "doctype",
					"name": "App Type"
				},
				{
					"type": "doctype",
					"name": "App Alert Device"
				},
				{
					"type": "doctype",
					"name": "Notification Tool"
				}
			]
		},
	]