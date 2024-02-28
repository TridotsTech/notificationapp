# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech Private Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json, os
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, parse_val, is_html
from frappe.utils.jinja import validate_template
from notification.notification.doctype.app_alert_settings.app_alert_settings import send_app_notification
from frappe.modules.utils import export_module_json, get_doc_module
from markdown2 import markdown
from six import string_types


class AppAlert(Document):
    def onload(self):
        '''load message'''
        if self.is_standard:
            self.message = self.get_template()
    def autoname(self):
        if not self.name:
            self.name = self.subject

    def validate(self):
        validate_template(self.subject)
        validate_template(self.message)

        if self.event in ("Days Before", "Days After") and not self.date_changed:
            frappe.throw(_("Please specify which date field must be checked"))

        if self.event=="Value Change" and not self.value_changed:
            frappe.throw(_("Please specify which value field must be checked"))

        self.validate_forbidden_types()
        self.validate_condition()
        self.validate_standard()

    def on_update(self):
        if 'ecommerce_business_store' in frappe.get_installed_apps():
            from ecommerce_business_store.ecommerce_business_store.api import update_custom_notification
            update_custom_notification('App Alert', self)
        frappe.cache().hdel('app_alerts', self.document_type)
        path = export_module_json(self, self.is_standard, self.module)
        if path:
            # js
            if not os.path.exists(path + '.md') and not os.path.exists(path + '.html'):
                with open(path + '.md', 'w') as f:
                    f.write(self.message)

            # py
            if not os.path.exists(path + '.py'):
                with open(path + '.py', 'w') as f:
                    f.write("""from __future__ import unicode_literals


import frappe

def get_context(context):
    # do your magic here
    pass
""")

    def on_trash(self):
        frappe.cache().hdel('app_alerts', self.document_type)
        check_notification = frappe.db.get_all('Custom Notification', filters={'notification_reference': self.name, 'reference_type': 'App Alert'})
        if check_notification:
            notification = frappe.get_doc('Custom Notification', check_notification[0].name)
            notification.delete()

    def validate_standard(self):
        if self.is_standard and not frappe.conf.developer_mode:
            frappe.throw(_('Cannot edit Standard App Alert. To edit, please disable this and duplicate it'))

    def validate_condition(self):
        temp_doc = frappe.new_doc(self.document_type)
        if self.condition:
            try:
                frappe.safe_eval(self.condition, None, get_context(temp_doc))
            except Exception:
                frappe.throw(_("The Condition '{0}' is invalid").format(self.condition))

    def validate_forbidden_types(self):
        forbidden_document_types = ("Email Queue",)
        if (self.document_type in forbidden_document_types
            or frappe.get_meta(self.document_type).istable):
            # currently App alerts don't work on child tables as events are not fired for each record of child table

            frappe.throw(_("Cannot set App Alert on Document Type {0}").format(self.document_type))

    def get_documents_for_today(self):
        '''get list of documents that will be triggered today'''
        docs = []

        diff_days = self.days_in_advance
        if self.event=="Days After":
            diff_days = -diff_days

        for name in frappe.db.sql_list("""select name from `tab{0}` where
            DATE(`{1}`) = ADDDATE(DATE(%s), INTERVAL %s DAY)""".format(self.document_type,
                self.date_changed), (nowdate(), diff_days or 0)):

            doc = frappe.get_doc(self.document_type, name)

            if self.condition and not frappe.safe_eval(self.condition, None, get_context(doc)):
                continue

            docs.append(doc)

        return docs

    def send(self, doc):
        '''Build recipients and send App alert'''

        context = get_context(doc)
        recipients = []
        for recipient in self.recipients:
            
            if recipient.condition:
                if not frappe.safe_eval(recipient.condition, None, context):
                    continue
            if recipient.app_alert_by_document_field:

                meta = frappe.get_meta(self.document_type)
                if recipient.app_alert_by_document_field=="owner":
                    device_ids = get_device_id(doc.doctype,doc.name)
                    for device_id in device_ids:
                        if device_id:
                            recipients = recipients + device_id.device_id.split("\n") 
                else:
                    field_type = frappe.get_meta(self.document_type).get_field(recipient.app_alert_by_document_field)
                    if field_type.fieldtype !="Dynamic Link":
                        for df in meta.get_link_fields():
                            if df.fieldname==recipient.app_alert_by_document_field:
                                if df.options and doc.get(recipient.app_alert_by_document_field):
                                    device_ids = get_device_id(df.options,doc.get(recipient.app_alert_by_document_field))
                                    for device_id in device_ids:
                                        if device_id:
                                            recipients = recipients + device_id.device_id.split("\n")

                    else:
                        device_ids = get_device_id(doc.get(field_type.options),doc.get(recipient.app_alert_by_document_field))
                        for device_id in device_ids:
                            if device_id:
                                recipients = recipients + device_id.device_id.split("\n")
                # if validate_email_add(doc.get(recipient.app_alert_by_document_field)):
                # recipient.app_alert_by_document_field = doc.get(recipient.app_alert_by_document_field).replace(",", "\n")
                # print(doc.get(recipient.app_alert_by_document_field).replace(",", "\n"))
                # recipients = recipients + recipient.app_alert_by_document_field.split("\n")
            
            if recipient.cc:
                recipient.cc = recipient.cc.replace(",", "\n")
                recipients = recipients + recipient.cc.split("\n")
            
            #For sending mobile number to specified role
            if recipient.app_alert_by_role:
                m_numbers = get_app_alert_from_role(recipient.app_alert_by_role, self, doc)
                for m_number in m_numbers:
                    if m_number:
                        recipients = recipients + m_number.split("\n") 
        if not recipients:
            return
        recipients = list(set(recipients))
        subject = self.subject

        context = {"doc": doc, "alert": self, "comments": None}

        if self.is_standard:
            self.load_standard_properties(context)

        if doc.get("_comments"):
            context["comments"] = json.loads(doc.get("_comments"))

        if "{" in subject:
            subject = frappe.render_template(self.subject, context)

        message=frappe.render_template(self.message,context)
        if recipients:
            try:
                path = frappe.local.request.url 
                if self.small_icon and self.small_icon.startswith("/files"):
                    self.small_icon = path+self.small_icon
                if self.large_icon and self.large_icon.startswith("/files"):
                    self.large_icon = path+self.large_icon
                if self.attach_image and self.attach_image.startswith("/files"):
                    self.attach_image = path+self.attach_image
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), str(e))
            send_app_notification(doc.doctype,doc.name,recipients, message,self.app_type,self.condition, self.small_icon, self.large_icon,self.attach_image,enable_channel_id=1)
        if self.set_property_after_alert:
            frappe.db.set_value(doc.doctype, doc.name, self.set_property_after_alert,
                self.property_value, update_modified = False)
            doc.set(self.set_property_after_alert, self.property_value)

    def get_template(self):
        module = get_doc_module(self.module, self.doctype, self.name)
        def load_template(extn):
            template = ''
            template_path = os.path.join(os.path.dirname(module.__file__),
                frappe.scrub(self.name) + extn)
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template = f.read()
            return template

        return load_template('.html') or load_template('.md')

    def load_standard_properties(self, context):
        '''load templates and run get_context'''
        module = get_doc_module(self.module, self.doctype, self.name)
        if module:
            if hasattr(module, 'get_context'):
                out = module.get_context(context)
                if out: context.update(out)

        self.message = self.get_template()

        if not is_html(self.message):
            self.message = markdown(self.message)

@frappe.whitelist()
def get_documents_for_today(email_alert):
    email_alert = frappe.get_doc('App Alert', email_alert)
    email_alert.check_permission('read')
    return [d.name for d in email_alert.get_documents_for_today()]

def trigger_daily_alerts():
    trigger_app_alerts(None, "daily")

def trigger_app_alerts(doc, method=None):
    if frappe.flags.in_import or frappe.flags.in_patch:
        # don't send App alerts while syncing or patching
        return

    if method == "daily":
        for alert in frappe.db.sql_list("""select name from `tabApp Alert`
            where event in ('Days Before', 'Days After') and enabled=1"""):
            alert = frappe.get_doc("App Alert", alert)
            for doc in alert.get_documents_for_today():
                evaluate_app_alert(doc, alert, alert.event)
                frappe.db.commit()

def evaluate_app_alert(doc, alert, event):
    from jinja2 import TemplateError
    try:
        if isinstance(alert, string_types):
            alert = frappe.get_doc("App Alert", alert)

        context = get_context(doc)
        if alert.condition:
            if not frappe.safe_eval(alert.condition, None, context):
                return
        
        if event=="Value Change" and not doc.is_new():
            try:
                db_value = frappe.db.get_value(doc.doctype, doc.name, alert.value_changed)
            except pymysql.InternalError as e:
                if e.args[0]== ER.BAD_FIELD_ERROR:
                    alert.db_set('enabled', 0)
                    frappe.log_error('App Alert {0} has been disabled due to missing field'.format(alert.name))
                    return

            db_value = parse_val(db_value)
            if (doc.get(alert.value_changed) == db_value) or \
                (not db_value and not doc.get(alert.value_changed)):

                return # value not changed

        if event != "Value Change" and not doc.is_new():
            # reload the doc for the latest values & comments,
            # except for validate type event.
            
            doc = frappe.get_doc(doc.doctype, doc.name)
        alert.send(doc)
    except TemplateError:
        frappe.throw(_("Error while evaluating App Alert {0}. Please fix your template.").format(alert))
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title=str(e))
        frappe.throw(_("Error in App Alert"))

def get_context(doc):
    return {"doc": doc, "nowdate": nowdate, "frappe.utils": frappe.utils}

# Get device ids of all users that have been assigned this role
def get_app_alert_from_role(role, self, doc):
    frappe.log_error(title="role", message=role)
    device_ids = [] 
    if role in ['Customer', 'Member', 'Driver']:
        dt = 'Customers'
        if role == 'Driver':
            dt = 'Drivers'
        elif role == 'Member':
            dt = 'Member'
        users_list = frappe.db.sql('''select name from `tab{}`'''.format(dt),as_dict=True)
        frappe.log_error(title="Customers", message=users_list)
        for usr in users_list:
            device_id= frappe.db.get_all("App Alert Device", filters={"document": dt, "user": usr.name, "enabled": 1}, fields=["device_id"])
            if device_id and len(device_id) > 0:
                device_ids.append(device_id[0].device_id)
        return device_ids
    if role in ['Sales Team']:
        frappe.log_error(title="in99",message=self.app_type) 
        if self.app_type=="SE App" and (self.document_type=="Order" or self.document_type=="Return Request") and doc.customer:
            centre = frappe.db.get_value("Customers", doc.customer, "center")
            frappe.log_error(title="centre",message=centre)
            employees = frappe.db.sql('''select name from `tabEmployee` where centre = "{centre}" and role in ("Sales Team")'''.format(centre=centre), as_dict=True)
            frappe.log_error(title="empl",message=employees)
            for usr in employees:
                device_id= frappe.db.get_all("App Alert Device", filters={"document": "Employee", "user": usr.name, "enabled": 1}, fields=["device_id"])
                if device_id and len(device_id) > 0:
                    device_ids.append(device_id[0].device_id)
        if self.app_type=="SE App" and (self.document_type=="Product"):
             employees = frappe.db.sql('''select name from `tabEmployee` where role in ("Sales Team")''', as_dict=True)
             for usr in employees:
                 device_id= frappe.db.get_all("App Alert Device", filters={"document": "Employee", "user": usr.name, "enabled": 1}, fields=["device_id"])
                 if device_id and len(device_id) > 0:
                      device_ids.append(device_id[0].device_id)
    users = frappe.db.get_all("Has Role", filters={"role": role, "parenttype": "User"},
        fields=["parent"])

    for user in users:
        device_id= frappe.db.get_all("App Alert Device", filters={"document": "User", "user": user.parent, "enabled": 1},
        fields=["device_id"])

        # mobile_no, enabled = frappe.db.get_value("User", user.parent, ["mobile_no", "enabled"])
        if len(device_id)>0:
            device_ids.append(device_id[0].device_id)
    return device_ids

# Get device ids of all users that have been assigned this role
def get_device_id(document,user):
    device = frappe.db.get_all("App Alert Device", filters={"document": document, "user": user, "enabled": 1},
        fields=["device_id","device_type"])
    return device
