# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech Private Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
from datetime import date,datetime,timedelta
import json
from requests.exceptions import HTTPError
from onesignalclient.app_client import OneSignalAppClient
from onesignalclient.notification import Notification

class AppAlertSettings(Document):
	pass

@frappe.whitelist()
def send_app_notification(reference_doc,name,player_ids,subject,reciever_type,condition, small_icon=None, large_icon=None, big_image=None, add_data=None, enable_sound=0,enable_channel_id=0,web_url=None):
	app_notification_settings=frappe.get_single('App Alert Settings')
	if app_notification_settings:
		if player_ids:
			app_name = reciever_type
			os_app_id = os_apikey = os_channel_id = None
			if app_notification_settings.keys:
				if "ecommerce_business_store" in frappe.get_installed_apps():
					from ecommerce_business_store.ecommerce_business_store.api import check_domain
					if not check_domain('saas'):
						check = next((x for x in app_notification_settings.keys if x.app_type == app_name),None)
					else:
						doc = frappe.get_doc(reference_doc, name)
						business = doc.get('business')
						if not business:
							business = doc.get('restaurant')
						check = next((x for x in app_notification_settings.keys if (x.app_type == app_name and x.business == business)),None)
						if not check:
							check = next((x for x in app_notification_settings.keys if x.app_type == app_name),None)
				else:
					check = next((x for x in app_notification_settings.keys if x.app_type == app_name),None)
				if check:
					os_app_id = check.app_id
					os_apikey = check.secret_key
					os_channel_id = check.channel_id
			if not os_apikey and not os_app_id:
				os_channel_id = app_notification_settings.channel_id
			if not os_apikey or not os_app_id:
				os_app_id = app_notification_settings.app_id
				os_apikey = app_notification_settings.secret_key
			if enable_channel_id == 0:
				os_channel_id = None
			# Init the client
			client = OneSignalAppClient(app_id=os_app_id, app_api_key=os_apikey)
			# Creates a new notification
			try:
				notification = Notification(os_app_id, Notification.DEVICES_MODE, enable_sound,os_channel_id)
			except Exception as e:
				notification = Notification(os_app_id, Notification.DEVICES_MODE)
			notification.include_player_ids = player_ids  # Must be a list!
			if add_data:
				notification.data = {'add_data': add_data}
			else:
				notification.data = {'add_data': name}
			if web_url:
				notification.web_url = web_url
			#icons and images
			if big_image:
				notification.big_picture = big_image
			if large_icon:
				notification.large_icon = large_icon
			if small_icon:
				notification.small_icon = small_icon
				
			notification.contents = {"en":subject}
			# if enable_sound:
			# notification.ios_sound = 'sound.wav'
			# notification.ios_badgeCount = 1
			# notification.ios_attachments = ''
			# notification.ios_attachments_type = ''
			# notification.ios_badgeType = 'None'
			# notification.ios_category = ''
			# notification.isIos = True
			# notification.isAndroid = True
			# notification.android_sound = 'sound.wav'
			# frappe.log_error(json.dumps(notification.__dict__), 'onesignal parameters')
			try:
				# Sends it!
				# raise ValueError('A very specific bad thing happened')
				result = client.create_notification(notification)
				update_history(reference_doc,name,subject,notification,reciever_type,condition)
				return {'message':'success'}
			except Exception as e:
				# result = e.response.json()
				frappe.log_error(frappe.get_traceback(), "notification.notification.doctype.app_alert_settings.app_alert_settings.send_app_notification")
				return {"message":"failed"}

def update_history(reference_doc,name,subject,notification,reciever_type,condition):
	history = frappe.new_doc("Notification History")
	history.reference = reference_doc
	history.reference_name = name
	history.subject = subject
	history.message = str(notification.contents)
	history.app_type = reciever_type
	history.action = ''
	history.value = condition
	history.player_ids = str(notification.include_player_ids)
	history.save(ignore_permissions=True)
	return history
