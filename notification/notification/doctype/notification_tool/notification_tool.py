# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech Private Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document

class NotificationTool(Document):
	pass

@frappe.whitelist()
def get_doctypes():
	return frappe.db.sql_list("""select name from tabDocType
		where module!='Core' order by name""")

@frappe.whitelist()
def update_alert(subject, doctype, send_alert_on, method=None, date_changed=None, days_in_advance=None, value_changed=None, conditions=None,filters_json=None, recipients=None, email_message=None,
set_property_after_email=None,property_value_email=None, if_email_by_field=None, email_by_document_field=None, sms_message=None, 
set_property_after_sms=None,property_value_sms=None, if_sms_by_field=None, sms_by_document_field=None, app_type=None, app_message=None, 
set_property_after_app=None,property_value_app=None, if_app_alert_by_field=None, app_alert_by_document_field=None):
	'''doctype, send_alert_on, filters_json, email_message, if_email_by_field, email_by_document_field, sms_message, if_sms_by_field, sms_by_document_field, app_message, if_app_alert_by_field, app_alert_by_document_field'''
	
	if json.loads(filters_json):
		cond=''
		for n in json.loads(filters_json):
			print(n[2])
			condition=n[2]
			if condition=="=":
				condition="=="
			cond = 'doc.'+n[1]+condition+'"'+n[3]+'"'
	else:
		cond = conditions
	if recipients:
			recipients = json.loads(recipients)
	if email_message:
		email = frappe.new_doc("Email Alert")
		email.subject = subject
		email.document_type = doctype
		email.event = send_alert_on
		email.method = method
		email.date_changed = date_changed
		email.days_in_advance = days_in_advance
		email.value_changed = value_changed
		# email.condition = conditions
		email.condition = cond

		email.message = email_message
		email.set_property_after_alert = set_property_after_email
		email.property_value = property_value_email
		if if_email_by_field==1 or if_email_by_field=="1":
			email.append("recipients",{"email_by_document_field":email_by_document_field,"email_by_role": "","cc": "", "condition": ""})
		if recipients:
			for rec in recipients:
				email.append("recipients",{"email_by_document_field":"","email_by_role": rec['by_role'],"cc": rec['cc'] , "condition": rec['condition']})
		email.save(ignore_permissions=True)
	if sms_message:
		email = frappe.new_doc("SMS Alert")
		email.subject = subject
		email.document_type = doctype
		email.event = send_alert_on
		email.method = method
		email.date_changed = date_changed
		email.days_in_advance = days_in_advance
		email.value_changed = value_changed
		# email.condition = conditions
		email.condition = cond
		email.message = sms_message
		email.set_property_after_alert = set_property_after_sms
		email.property_value = property_value_sms
		if if_sms_by_field==1 or if_sms_by_field=="1":
			email.append("recipients",{"sms_by_document_field":sms_by_document_field,"sms_by_role": "","cc": "", "condition": ""})
		if recipients:
			for rec in recipients:
				email.append("recipients",{"sms_by_document_field":"","sms_by_role": rec['by_role'],"cc": rec['cc'] , "condition": rec['condition']})
		email.save(ignore_permissions=True)
	if app_message:
		email = frappe.new_doc("App Alert")
		email.subject = subject
		email.document_type = doctype
		email.app_type = app_type
		email.event = send_alert_on
		email.method = method
		email.date_changed = date_changed
		email.days_in_advance = days_in_advance
		email.value_changed = value_changed
		# email.condition = conditions
		email.condition = cond
		email.message = app_message
		email.set_property_after_alert = set_property_after_app
		email.property_value = property_value_app
		if if_app_alert_by_field==1 or if_app_alert_by_field=="1":
			email.append("recipients",{"app_alert_by_document_field":app_alert_by_document_field,"app_alert_by_role": "","cc": "", "condition": ""})
		if recipients:
			for rec in recipients:
				email.append("recipients",{"app_alert_by_document_field":"","app_alert_by_role": rec['by_role'],"cc": rec['cc'] , "condition": rec['condition']})
		email.save(ignore_permissions=True)

	return doctype