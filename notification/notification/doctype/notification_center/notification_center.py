# -*- coding: utf-8 -*-
# Copyright (c) 2018, Tridots Tech and contributors
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
from frappe.utils import  cint, flt, parse_val, is_html, add_months, today, date_diff, getdate, add_days, cstr, nowdate, make_filter_tuple
from six import string_types
from frappe.model.db_query import DatabaseQuery

class NotificationCenter(Document):
	pass

def convert_json_conditions(filters, doctype, condition):
	exclude = ["sum_g","sum_l", "sum_e", "count_g","count_l", "count_e", "average_g","average_l", "average_e"]
	if filters:
		filters = json.loads(filters)
	condition = ''
	c_condition = ''
	if filters:
		for f in filters:
			fl = get_filter_condition(f, doctype)
			if fl.operator not in exclude:
				# frappe.log_error("", "=======")
				db_service = DatabaseQuery(doctype=doctype)
				db_service.flags.ignore_permissions = True
				cond = db_service.prepare_filter_condition(f)
				if cond:
					condition += ' and {0}'.format(cond)
			else:
				if "having" in c_condition:
					prefix ="and"
				else:
					prefix ="having"
				exclude_field=get_exclude_condition(fl.operator)
				tname = ('`tab' + fl.doctype + '`')
				if 'ifnull(' in fl.fieldname:
					column_name = fl.fieldname
				else:
					column_name = '{tname}.{fname}'.format(tname=tname,
						fname=fl.fieldname)
				cond = ' {prefix} (select {operation}({column_name}) from {table}) {condition} {value}'.format(
					prefix=prefix,column_name=column_name, table= tname, operation=exclude_field['operation'], 
					condition=exclude_field['condition'], value=fl.value)
				if cond:
					c_condition += '{0}'.format(cond)
	condition += c_condition
	# frappe.msgprint(frappe._("{0}").format(str(condition)))
	return condition

def get_filter_condition(f, doctype):
	from frappe.model import default_fields, optional_fields
	if isinstance(f, dict):
		key, value = next(iter(f.items()))
		f = make_filter_tuple(doctype, key, value)

	if len(f) == 3:
		f = (doctype, f[0], f[1], f[2])

	elif len(f) > 4:
		f = f[0:4]
	
	f = frappe._dict(doctype=f[0], fieldname=f[1], operator=f[2], value=f[3])

	if not f.operator:
		# if operator is missing
		f.operator = "="

	if f.doctype and (f.fieldname not in default_fields + optional_fields):
		# verify fieldname belongs to the doctype
		meta = frappe.get_meta(f.doctype)
		if not meta.has_field(f.fieldname):
			# try and match the doctype name from child tables
			for df in meta.get_table_fields():
				if frappe.get_meta(df.options).has_field(f.fieldname):
					f.doctype = df.options
					break
	return f

def get_exclude_condition(operator):
	cond = [{"operator": "sum_g", "operation": "sum", "condition": ">"},
	{"operator": "sum_l", "operation": "sum", "condition": "<"},
	{"operator": "sum_e", "operation": "sum", "condition": "="},
	{"operator": "count_g", "operation": "count", "condition": ">"},
	{"operator": "count_l", "operation": "count", "condition": "<"},
	{"operator": "count_e", "operation": "count", "condition": "="},
	{"operator": "average_g", "operation": "avg", "condition": ">"},
	{"operator": "average_l", "operation": "avg", "condition": "<"},
	{"operator": "average_e", "operation": "avg", "condition": "="}]
	for obj in cond:
		if obj['operator'] == operator:
			return obj

@frappe.whitelist()
def insert_notification(name,message,table_5,device_ids, reciever_type=None):
	notification={}
	notification["contents"]= message
	notification["include_player_ids"]= device_ids
	if reciever_type:
		reciever_type=reciever_type
	else:
		reciever_type=""
	condition=""
	update_notification_history("Notification Center","Notification Center",name,notification,reciever_type,condition)

@frappe.whitelist()
def get_random():
	import random 
	import string
	random = ''.join([random.choice(string.ascii_letters
            + string.digits) for n in range(6)])
	Name=frappe.db.get_all('Notification',fields=['name'])
	for x in Name:
		if x.name==random:
			random=get_random()
	return random

def get_conditions(filters_json, doctype, condition=""):
	return convert_json_conditions(filters_json, doctype, condition)
	# if filters_json:
	# 	filters = json.loads(filters_json)
	# 	condition += convert_json_conditions(filters, doctype, condition)


@frappe.whitelist()
def get_device_ids(party_type, filters_json):
	user_list = []
	# filters={"name": ("!=", "")}
	condition = get_conditions(filters_json, party_type)
	# if party:
		# filters["name"] = party
	# frappe.log_error(party_type, "party_type")
	if party_type == "Customers":
		business_condition = ""
		# frappe.log_error("party_type", "party_type----")
		from ecommerce_business_store.ecommerce_business_store.api import check_domain
		from ecommerce_business_store.utils.setup import get_business_from_web_domain
		if check_domain("saas"):
			domain = frappe.get_request_header('host')
			business = get_business_from_web_domain(domain)
			if business:
				business_condition = "AND `tabCustomers`.business='{0}'".format(business)

		query = '''select distinct `tab{doctype}`.name as c_name, `tab{doctype}`.* from `tab{doctype}` left join `tabCustomer Address` on `tabCustomer Address`.parent=`tab{doctype}`.name left join `tabCustomer Viewed Product` on `tabCustomer Viewed Product`.parent=`tab{doctype}`.name left join `tabCustomer Preference` on `tabCustomer Preference`.parent=`tab{doctype}`.name left join `tabCustomer Role` on `tabCustomer Role`.parent=`tab{doctype}`.name where `tab{doctype}`.name != "" {business_condition} {condition}'''.format(doctype=party_type,business_condition=business_condition,condition=condition)
		# frappe.log_error(query, "query")
		party_list = frappe.db.sql(query,as_dict=1)

		# party_list = frappe.db.get_all(party_type,fields=['name','user_id'], filters=filters)
		role = "Customer"
	elif party_type == "Drivers":
		party_list = frappe.db.sql('''select * from `tab{doctype}` left join `tabDriver Business Mapping` on `tabDriver Business Mapping`.parent=`tab{doctype}`.name where `tab{doctype}`.name != "" {condition}'''.format(doctype=party_type, condition=condition),as_dict=1)

		# party_list = frappe.db.get_all(party_type,fields=['name'], filters=filters)
		role = "Driver"
	elif party_type == "Business":
		party_list = frappe.db.sql('''select * from `tab{doctype}` where `tab{doctype}`.name != "" {condition}'''.format(doctype=party_type, condition=condition),as_dict=1)
		# party_list = frappe.db.get_all("User",fields=['name'], filters=filters)
		role = "Vendor"
	else:
		# party_list = frappe.db.get_all(party_type,fields=['name'], filters=filters)
		party_list = frappe.db.sql('''select * from `tab{doctype}` where `tab{doctype}`.name != "" {condition}'''.format(doctype=party_type, condition=condition),as_dict=1)
		role = "Guest"
	if party_list:
		for party_name in party_list:
			user = party_name.name
			if party_type == "Customers":
				user = party_name.user_id
			else:
				user = party_name.name 
			player_id = frappe.db.sql('''select distinct device_id from `tabApp Alert Device` where document=%(party_type)s and user=%(user)s''',{'user':party_name.name,"party_type":party_type},as_dict=1)
			if len(player_id) >0:
				party_name['device_id'] = player_id[0].device_id
				user_list.append({"name":party_name.name,"device_id":party_name.device_id})
			else:
				party_name['player_id'] = None

	return user_list

@frappe.whitelist()
def get_items(url):
	now=getdate(nowdate())
	if frappe.db.get_value("DocType", url):
		if url=='Events':
			data=frappe.db.sql('''select name from `tabEvents` where start_date>=%(now)s''',{'now':nowdate()},as_dict=1)
			return data
		elif url=='Samaj Darshan':
			data=frappe.db.get_all('Samaj Darshan',fields=['name','year'],filters={'year':now.year})
			for item in data:
				item.list=frappe.db.get_all('Samaj Darshan Lists',fields=['*'],filters={'parent':item.name,'published':0})
			return data
		else:
			data=frappe.db.get_all(url,fields=['*'])
			return data

@frappe.whitelist()
def update_notification_history(reference_doc,name,subject,notification,reciever_type,condition):
	history = frappe.new_doc("Notification History")
	history.reference = reference_doc
	history.reference_name = name
	history.subject = subject
	history.message = str(notification['contents'])
	history.app_type = reciever_type
	history.action = ''
	history.value = condition
	history.player_ids = str(notification['include_player_ids'])
	history.save(ignore_permissions=True)
	return history


@frappe.whitelist()
def delete_attached_images(attach_image=None, large_icon=None, small_icon=None):
	if attach_image:
		if frappe.db.exists("File", {"file_url":attach_image, "attached_to_doctype":"Notification Center"}):
			attach = frappe.db.get_value("File",{"file_url":attach_image, "attached_to_doctype":"Notification Center", "attached_to_name":"Notification Center"})
			frappe.db.set_value("File", attach,"attached_to_doctype","")
			frappe.db.set_value("File", attach,"attached_to_name","")
	if large_icon:
		if frappe.db.exists("File", {"file_url":large_icon, "attached_to_doctype":"Notification Center"}):
			large = frappe.db.get_value("File",{"file_url":large_icon, "attached_to_doctype":"Notification Center", "attached_to_name":"Notification Center"})
			frappe.db.set_value("File", large,"attached_to_doctype","")
			frappe.db.set_value("File", large,"attached_to_name","")
		
	if small_icon:
		if frappe.db.exists("File", {"file_url":small_icon, "attached_to_doctype":"Notification Center"}):
			small = frappe.db.get_value("File",{"file_url":small_icon, "attached_to_doctype":"Notification Center", "attached_to_name":"Notification Center"})
			frappe.db.set_value("File", small,"attached_to_doctype","")
			frappe.db.set_value("File", small,"attached_to_name","")

@frappe.whitelist()
def get_settings():
	app_notification_settings=frappe.get_single('App Alert Settings')
	from ecommerce_business_store.ecommerce_business_store.api import check_domain
	from ecommerce_business_store.utils.setup import get_business_from_web_domain
	if check_domain("saas"):
		domain = frappe.get_request_header('host')
		business = get_business_from_web_domain(domain)
		if business:
			api_keys = []
			for x in app_notification_settings.keys:
				if x.get("business") == business:
					api_keys.append(x)
			app_notification_settings.keys = api_keys
	return app_notification_settings

