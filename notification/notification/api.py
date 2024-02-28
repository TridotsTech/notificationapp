# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech Private Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from six import string_types
from frappe import _, throw, msgprint
from frappe.utils import nowdate, now, today
from frappe.utils import getdate, add_to_date, time_diff_in_hours
from datetime import date, datetime, timedelta
from six import string_types
from frappe.utils import validate_email_address, nowdate, parse_val, is_html, add_to_date
from frappe.utils.jinja import validate_template
from frappe.modules.utils import export_module_json, get_doc_module
from frappe.core.doctype.sms_settings.sms_settings import validate_receiver_nos, get_headers, send_request
from frappe.utils import cstr

@frappe.whitelist(allow_guest=True)
def update_user_device_id(document, user, device_id, device_type='Mobile', enabled=1, role=None):
	check_entry = frappe.get_all('App Alert Device', filters={ 'document': document, 'user': user, 'device_type': device_type })
	if check_entry:
		doc = frappe.get_doc('App Alert Device', check_entry[0].name)
	else:
		doc = frappe.new_doc('App Alert Device')
		doc.document = document
		doc.user = user
		doc.device_type = device_type
	if device_id and device_id not in ['undefined', 'null']:
		doc.device_id = device_id
	doc.role = role
	doc.enabled = enabled
	doc.save(ignore_permissions=True)
	return doc

def on_submit_order(doc, method):
	if doc.business:
		openings = check_business_opening(doc.business)
		print(openings)
		if openings:
			vendors = frappe.db.get_all('Shop User', filters={'restaurant': doc.business, 'role': 'Vendor'})
			if vendors:
				for vendor in vendors:
					insert_notification_queue('Order', doc.name, vendor.name)

# check for business_opening
@frappe.whitelist(allow_guest=True)
def check_business_opening(business):
	if business:
		time_zone = frappe.db.get_single_value('System Settings','time_zone')
		dtfmt = '%Y-%m-%d %H:%M:%S'
		if 'ecommerce_business_store' in frappe.get_installed_apps():
			from ecommerce_business_store.ecommerce_business_store.api import get_today_date
			currentdatezone = get_today_date(time_zone, True)
		else:
			currentdatezone = today()
		today_date = getdate(currentdatezone)
		day = getdate(today_date).strftime('%A')
		timings = frappe.db.sql('''select day, from_hrs as from_time, to_hrs as to_time from `tabOpening Hour` where parent = %(parent)s and status = "Open"''', {'parent': business}, as_dict=1)
		if timings:
			check_day = list(filter(lambda x: x.day == day, timings))
			if check_day: 
				return check_day
			else:
				return None
		else:
			return None
	
def insert_notification_queue(document, reference_name, shop_user=None, customer=None, content=None):
	queue = frappe.get_doc({
		"doctype": "Notification Queue",
		"document": document,
		"reference_name": reference_name,
		"shop_user": shop_user	
		})
	if shop_user:
		queue.shop_user = shop_user
	if customer:
		queue.customer = customer
	if content:
		queue.content = content
	queue.insert(ignore_permissions=True)



@frappe.whitelist()
def send_sms_to_receivers(receiver_list, msg, sender_name = '', success_msg = True, from_sms=None):
	if not from_sms:
		from_sms = "SMS Center"
	if isinstance(receiver_list, string_types):
		receiver_list = json.loads(receiver_list)
		if not isinstance(receiver_list, list):
			receiver_list = [receiver_list]
	if isinstance(msg, str):
		text = msg
		decoded = False
	else:
		text = msg.decode(encoding)
		decoded = True
	receiver_list = validate_receiver_nos(receiver_list)
	# unicode(msg).encode('utf-8')
	arg = {
		'receiver_list' : receiver_list,
		'message'		: msg.encode('utf-8'),
		'success_msg'	: success_msg
	}
	
	if frappe.db.get_value('SMS Settings', None, 'sms_gateway_url'):
		send_via_gateway_sms(arg, from_sms)
	else:
		msgprint(_("Please Update SMS Settings"))


# send SMS by siva 
def send_via_gateway_sms(arg, from_sms):
	ss = frappe.get_doc('SMS Settings', 'SMS Settings')
	headers = get_headers(ss)
	args = {ss.message_parameter: arg.get('message')}
	for d in ss.get("parameters"):
		if not d.header:
			args[d.parameter] = d.value
	ss.use_post = 1
	from frappe.utils.background_jobs import enqueue, get_jobs
	status = enqueue('notification.notification.api.send_request_custom',
				gateway_url=ss.sms_gateway_url, params=args, arg=arg, from_sms=from_sms, headers=headers, use_post=ss.use_post, queue='short')
	
def send_request_custom(gateway_url, params, arg, from_sms, headers=None, use_post=False):
	try:
		success_list = []
		ss = frappe.get_doc('SMS Settings', 'SMS Settings')
		for d in arg.get('receiver_list'):
			params[ss.receiver_parameter] = d
			import requests
			if not headers:
				headers = get_headers()
			if use_post:
				response = requests.post(gateway_url, headers=headers, data=params)
			else:
				response = requests.get(gateway_url, headers=headers, params=params, verify=False)
			msg = "URL :"+str(gateway_url)+"\nHeader :"+ str(headers) +"\nParams :"+ str(params) +"\nResponse: "+str(response)
			frappe.log_error(msg, gateway_url)	
			response.raise_for_status()
			if 200 <= response.status_code < 300:
				success_list.append(d)
		if len(success_list) > 0:
			params.update(arg)
			create_sms_log(params, success_list, from_sms)
			if arg.get('success_msg'):
				res_list = " ".join(['<li>' + x + '</li>' for x in success_list])
			# 	frappe.publish_realtime(event='msgprint', message=_("<b>SMS sent to following numbers:</b>\n<ul>{0}</ul>").format(res_list), user=frappe.session.user,doctype='SMS Logs')
				frappe.msgprint(_("<b>SMS sent to following numbers:</b>\n<ul>{0}</ul>").format(res_list))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "notification.notification.api.send_request_custom")	

# Create SMS Log
# =========================================================
def create_sms_log(args, sent_to, from_sms=None):
	try:
		sl = frappe.new_doc('SMS Logs')
		sl.sender_name = "Admin"
		sl.sent_on = now()
		sl.message = args['message'].decode('utf-8')
		sl.no_of_requested_sms = len(args['receiver_list'])
		sl.requested_numbers = "\n".join(args['receiver_list'])
		sl.no_of_sent_sms = len(sent_to)
		sl.sent_to = "\n".join(sent_to)
		sl.from_sms = from_sms
		sl.flags.ignore_permissions = True
		sl.save()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "notification.notification.api.create_sms_log")	


#get user based notification history
# ========================================
@frappe.whitelist()
def get_notification_log(party=None, user=None, page_no=None, page_len=None):
	if page_no and page_len:
		start = (int(page_no) - 1) * int(page_len)
		history_list=frappe.db.sql('''select * from `tabNotification History` limit {start},{limit}'''.format(start=start, limit=page_len))
	else:
		history_list = frappe.db.get_all("Notification History", fields=["*"])
	
	notifications=[]
	if user:
		player_id = frappe.db.sql('''select device_id from `tabApp Alert Device` where document=%(party)s and user=%(user)s''',{'user':user,"party":party},as_dict=1)
		if len(player_id) >0:
			device = player_id[0].device_id
			from six import string_types
			for x in history_list:
				pid = x['player_ids']
				if pid:
					if device in pid:
						notifications.append(x)
				# if x and x['player_ids']:
				# 	if isinstance(x['player_ids'], string_types): 
				# 		pid = json.loads(x['player_ids'])
				# 	else:
				# 		pid = x['player_ids']
				# 	if device in pid:
				# 		notifications.append(x)
			# today_timings = list(filter(lambda x: device in pid  if isinstance(x['player_ids'], string_types)  pid = json.loads(x['player_ids']) else pid = x['player_ids'], history_list))
			# notifications.append(today_timings)
	else:
		notifications=history_list
	return notifications

def update_user_payer_id(doc, method):
	allowed = True
	if doc.doctype == "Customers":
		if doc.full_name == "Guest":
			allowed = False
	if allowed:	
		check_device_id = frappe.db.get_all('App Alert Device', filters={'document': doc.doctype, 'user': doc.name})
		if check_device_id and doc.player_id:
			frappe.db.set_value('App Alert Device', check_device_id[0].name, 'device_id', doc.player_id)
		elif not check_device_id and doc.player_id:
			update_user_device_id(doc.doctype, doc.name, doc.player_id)
		elif check_device_id and not doc.player_id:
			frappe.db.set_value('App Alert Device', check_device_id[0].name, 'enabled', 0)

# def get_today_date(time_zone=None, replace=False):
# 	'''
# 		get today  date based on selected time_zone
# 	'''

# 	if not time_zone:
# 		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
# 	currentdate = datetime.now()
# 	currentdatezone = datetime.now(timezone(time_zone))
# 	if replace:
# 		return currentdatezone.replace(tzinfo=None)
# 	else:
# 		return currentdatezone

#created by sivaranjani
@frappe.whitelist()	
def send_notification_mail(notification, doc, receivers=None, context=None):
	try:
		alert = frappe.get_doc("Notification", notification)
		context = {"doc": doc, "alert": alert, "comments": None}
		from email.utils import formataddr
		subject = alert.subject
		if "{" in subject:
			subject = frappe.render_template(alert.subject, context)

		attachments = alert.get_attachment(doc)
		attachments=""
		receiver_list=None
		if receivers:
			receiver_list=receivers
		recipients, cc, bcc = get_list_of_recipients(alert, receiver_list, doc, context)
		if not (recipients or cc or bcc):
			return
		sender = None
		if alert.sender and alert.sender_email:
			sender = formataddr((alert.sender, alert.sender_email))
		frappe.sendmail(recipients = recipients,
			subject = subject,
			sender = sender,
			cc = cc,
			bcc = bcc,
			message = frappe.render_template(alert.message, context),
			reference_doctype = doc.doctype,
			reference_name = doc.name,
			attachments = attachments,
			expose_recipients="header",
			print_letterhead = ((attachments
				and attachments[0].get('print_letterhead')) or False))
	except Exception as e:		
		frappe.log_error(frappe.get_traceback(), "notification.notification.api.send_notification_mail")

def get_context(doc):
	return {"doc": doc, "nowdate": nowdate, "frappe": frappe._dict(utils=frappe.utils)}


def get_list_of_recipients(alert, receiver_list, doc, context):
	recipients = []
	cc = []
	bcc = []
	for recipient in alert.recipients:
		if recipient.condition:
			if not frappe.safe_eval(recipient.condition, None, context):
				continue
		if recipient.email_by_document_field:
			email_ids_value = doc.get(recipient.email_by_document_field)
			if validate_email_address(email_ids_value):
				email_ids = email_ids_value.replace(",", "\n")
				recipients = recipients + email_ids.split("\n")

			# else:
			# 	print "invalid email"
		if recipient.cc and "{" in recipient.cc:
			recipient.cc = frappe.render_template(recipient.cc, context)

		if recipient.cc:
			recipient.cc = recipient.cc.replace(",", "\n")
			cc = cc + recipient.cc.split("\n")

		if recipient.bcc and "{" in recipient.bcc:
			recipient.bcc = frappe.render_template(recipient.bcc, context)

		if recipient.bcc:
			recipient.bcc = recipient.bcc.replace(",", "\n")
			bcc = bcc + recipient.bcc.split("\n")
			
		#For sending emails to specified role
		if recipient.email_by_role:
			emails = get_emails_from_role(recipient.email_by_role)

			for email in emails:
				recipients = recipients + email.split("\n")

		contact_emails = frappe.db.get_single_value('Admin Settings', 'contact_email')
		if contact_emails:
			recipients = recipients + contact_emails.split("\n")
	if receiver_list:
		for rec in receiver_list:
			recipients = recipients + rec.split("\n")
	
	if not recipients and not cc and not bcc:
		return None, None, None
	return list(set(recipients)), list(set(cc)), list(set(bcc))

def get_attachment(alert, doc):
	""" check print settings are attach the pdf """
	if not alert.attach_print:
		return None

	print_settings = frappe.get_doc("Print Settings", "Print Settings")
	if (doc.docstatus == 0 and not print_settings.allow_print_for_draft) or \
		(doc.docstatus == 2 and not print_settings.allow_print_for_cancelled):

		# ignoring attachment as draft and cancelled documents are not allowed to print
		status = "Draft" if doc.docstatus == 0 else "Cancelled"
		frappe.throw(_("""Not allowed to attach {0} document,
			please enable Allow Print For {0} in Print Settings""".format(status)),
			title=_("Error in Notification"))
	else:
		return [{
			"print_format_attachment": 1,
			"doctype": doc.doctype,
			"name": doc.name,
			"print_format": alert.print_format,
			"print_letterhead": print_settings.with_letterhead,
			"lang": frappe.db.get_value('Print Format', alert.print_format, 'default_print_language')
				if alert.print_format else 'en'
		}]

# Get email addresses of all users that have been assigned this role
def get_emails_from_role(role):
	emails = []

	users = frappe.get_list("Has Role", filters={"role": role, "parenttype": "User"},
		fields=["parent"])

	for user in users:
		user_email, enabled = frappe.db.get_value("User", user.parent, ["email", "enabled"])
		if enabled and user_email not in ["admin@example.com", "guest@example.com"]:
			emails.append(user_email)

	return emails

@frappe.whitelist()
def send_custom_sms(receiver_list, message, content_id=None,context=None):
	# from frappe.core.doctype.sms_settings.sms_settings import send_sms

	if receiver_list and message:
		send_sms(receiver_list, cstr(message), content_id,context)

@frappe.whitelist()
def send_sms(receiver_list, msg, content_id = None,context=None, sender_name = '', success_msg = True):
	
	import json
	if isinstance(receiver_list, string_types):
		receiver_list = json.loads(receiver_list)
		if not isinstance(receiver_list, list):
			receiver_list = [receiver_list]
	receiver_list = validate_receiver_nos(receiver_list)
	arg = {
		'receiver_list' : receiver_list,
		'message'		: frappe.safe_decode(msg).encode('utf-8'),
		'content_id'	: (content_id),
		'success_msg'	: success_msg
	}
	frappe.log_error(title="sms log",message=arg)
	if frappe.db.get_value('SMS Settings', None, 'sms_gateway_url'):
		send_via_gateway(arg,context)
	else:
		msgprint(_("Please Update SMS Settings"))

def send_via_gateway(arg,context=None):
	frappe.log_error(context,'context')
	from urllib.parse import urljoin, unquote, urlencode
	ss = frappe.get_doc('SMS Settings', 'SMS Settings')
	headers = get_headers(ss)
	args = {ss.message_parameter: arg.get('message')}
	if arg.get('content_id'):
		args[ss.content_id] =unquote(arg.get('content_id'))
	check_params = []
	for d in ss.get("parameters"):
		if not d.header:
			args[d.parameter] = d.value
	if context:
		for d in context.get("alert").get("parameters"):
			if "{{" in d.value:
				if not "{{" in  frappe.render_template(d.value, context):
					args[d.parameter] = frappe.render_template(d.value, context)

			else:
				args[d.parameter] = d.value


	success_list = []
	for d in arg.get('receiver_list'):
		args[ss.receiver_parameter] = d
		try:
			status = send_request(unquote(ss.sms_gateway_url),(args), headers, ss.use_post)
			if 200 <= status < 300:
				success_list.append(d)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "send_request")

	if len(success_list) > 0:
		args.update(arg)
		create_sms_log(args, success_list)
		if arg.get('success_msg'):
			frappe.msgprint(_("SMS sent to following numbers: {0}").format("\n" + "\n".join(success_list)))

#created by sivaranjani
@frappe.whitelist()	
def send_admin_notification_mail(notification, doc, receivers=None, context=None, message=None, subject=None):
	try:
		alert = frappe.get_doc("Notification", notification)
		context = {"doc": doc, "alert": alert, "comments": None}
		from email.utils import formataddr
		if not subject:
			subject = alert.subject
			if "{" in subject:
				subject = frappe.render_template(alert.subject, context)

		attachments = alert.get_attachment(doc)
		attachments=""
		receiver_list=None
		if receivers:
			receiver_list=receivers
		recipients, cc, bcc = get_list_of_recipients(alert, receiver_list, doc, context)
		if not (recipients or cc or bcc):
			return
		sender = None
		if alert.sender and alert.sender_email:
			sender = formataddr((alert.sender, alert.sender_email))
		frappe.sendmail(recipients = recipients,
			subject = subject,
			sender = sender,
			cc = cc,
			bcc = bcc,
			message = message,
			reference_doctype = doc.doctype,
			reference_name = doc.name,
			attachments = attachments,
			expose_recipients="header",
			print_letterhead = ((attachments
				and attachments[0].get('print_letterhead')) or False))
	except Exception as e:		
		frappe.log_error(frappe.get_traceback(), "notification.notification.api.send_notification_mail")

def create_sms_settings_custom_field():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_field, create_custom_fields
	custom_fields = {
		'SMS Settings': [
			dict(fieldname='content_id', label='Content ID',
			fieldtype='Data', insert_after='receiver_parameter', translatable=0)
			]
	}
	create_custom_fields(custom_fields)

@frappe.whitelist()
def send_app_alerts(doc,method):
	if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install:
		return
	if doc.flags.app_alerts_executed==None:
		doc.flags.app_alerts_executed = []
	from notification.notification.doctype.app_alert.app_alert import evaluate_app_alert
	if doc.flags.app_alerts == None:
		alerts = frappe.cache().hget('app_alerts', doc.doctype)
		if alerts==None or len(alerts)==0:
			alerts = frappe.get_all('App Alert', fields=['name', 'event', 'method'],
				filters={'enabled': 1, 'document_type': doc.doctype})
			frappe.cache().hset('app_alerts', doc.doctype, alerts)
		doc.flags.app_alerts = alerts

	if not doc.flags.app_alerts:
		return

	def _evaluate_app_alert(alert):
		if not alert.name in doc.flags.app_alerts_executed:
			evaluate_app_alert(doc, alert.name, alert.event)
			doc.flags.app_alerts_executed.append(alert.name)

	event_map = {
		"on_update": "Save",
		"after_insert": "New",
		"on_submit": "Submit",
		"on_cancel": "Cancel"
	}

	if not doc.flags.in_insert:
		# value change is not applicable in insert
		event_map['validate'] = 'Value Change'
		event_map['before_change'] = 'Value Change'
		event_map['before_update_after_submit'] = 'Value Change'

	for alert in doc.flags.app_alerts:
		event = event_map.get(method, None)
		if event and alert.event == event:
			_evaluate_app_alert(alert)
		elif alert.event=='Method' and method == alert.method:
			_evaluate_app_alert(alert)

