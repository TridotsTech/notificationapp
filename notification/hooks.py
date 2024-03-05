# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "notification"
app_title = "Notification"
app_publisher = "Tridots Tech Private Ltd."
app_description = "for sms, email and mobile notification"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@valiantsystems.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/notification/css/notification.css"
# app_include_js = "/assets/notification/js/notification.js"
after_install = "notification.notification.api.create_sms_settings_custom_field"
# include js, css files in header of web template
# web_include_css = "/assets/notification/css/notification.css"
# web_include_js = "/assets/notification/js/notification.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

scheduler_events = {
	"cron": {
		"0 0 * * *": [
			"notification.notification.doctype.sms_alert.sms_alert.trigger_daily_alerts",
			"notification.notification.doctype.app_alert.app_alert.trigger_daily_alerts"
		]
	}
}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "notification.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "notification.install.before_install"
# after_install = "notification.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "notification.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	("Customers", "Drivers"): {
		"on_update": "notification.notification.api.update_user_payer_id"
	},
	"*":{
		"on_update": "notification.notification.api.send_app_alerts",
        # "on_update_after_submit": "notification.notification.api.send_app_alerts",
		# "after_insert": "notification.notification.api.send_app_alerts",
		# "on_submit": "notification.notification.api.send_app_alerts",
		# "on_cancel": "notification.notification.api.send_app_alerts",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"notification.tasks.all"
# 	],
# 	"daily": [
# 		"notification.tasks.daily"
# 	],
# 	"hourly": [
# 		"notification.tasks.hourly"
# 	],
# 	"weekly": [
# 		"notification.tasks.weekly"
# 	]
# 	"monthly": [
# 		"notification.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "notification.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.core.doctype.sms_settings.sms_settings.send_sms": "notification.notification.api.send_sms"
}

