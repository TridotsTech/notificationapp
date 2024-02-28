# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe import _, throw, msgprint
from frappe.utils import nowdate

from frappe.model.document import Document
from six import string_types

class SMSLogs(Document):
	pass