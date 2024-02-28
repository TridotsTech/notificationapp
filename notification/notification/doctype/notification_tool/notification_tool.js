// Copyright (c) 2019, Tridots Tech Private Ltd. and contributors
// For license information, please see license.txt
frappe.require('assets/frappe/js/frappe/ui/filters/filter.js');
frappe.ui.form.on('Notification Tool', {
	
	select_doctype: function(frm) {
		// update `based_on` options based on date / datetime fields
		frm.set_value('filters_json', '[]');
		frm.trigger('update_options');
		if(frm.doc.select_doctype){
			frm.set_df_property("sec_0", "hidden", 0);
			frm.set_df_property("sec_1", "hidden", 0);
			frm.set_df_property("sec_2", "hidden", 0);
			frm.set_df_property("sec_3", "hidden", 0);
			frm.trigger("alert_by_field");
		}
	},
	send_alert_on: function(frm){
		if(frm.doc.select_doctype){
			frm.trigger("alert_by_field");
		}
	},
	refresh: function(frm) {
		
		if(cur_frm.doc.filters_json=="[]" || cur_frm.doc.filters_json==undefined || cur_frm.doc.filters_json==""){
			frm.set_df_property("add_filter","hidden",0)
		}
		else{
			frm.set_df_property("add_filter","hidden",1)
		}
		frm.disable_save();
		frm.trigger('update_options');
		frm.notification_filters = null;
		frm.set_df_property("filters_section", "hidden", 1);
		let wrapper = $(frm.get_field('filter_html').wrapper).empty();
		wrapper.append('<div class="filter-edit-area"></div>');
		if(!frm.doc.select_doctype){
			frm.set_df_property("sec_0", "hidden", 1);
			frm.set_df_property("sec_1", "hidden", 1);
			frm.set_df_property("sec_2", "hidden", 1);
			frm.set_df_property("sec_3", "hidden", 1);
			
		}
		else{
			frm.set_df_property("sec_0", "hidden", 0);
			frm.set_df_property("sec_1", "hidden", 0);
			frm.set_df_property("sec_2", "hidden", 0);
			frm.set_df_property("sec_3", "hidden", 0);
			frm.trigger("alert_by_field");
		}

		frm.page.set_primary_action(__('Update'), function() {
			if(!frm.doc.select_doctype){
				frappe.throw(__('Field "DocType" is mandatory. Please specify value to be updated'));
			}
			else{
				recipients=[]
				$.each(frm.doc.recipients,function(i, v){
					let item={}
					if(v.by_role)
						item.by_role=v.by_role
					else
						item.by_role=""
					if(v.cc)
						item.cc=v.cc
					else
						item.cc=""
					if(v.condition)
						item.condition=v.condition
					else
						item.condition=""
					recipients.push(item)

				})
				
				if(frm.doc.email_message!=undefined || frm.doc.sms_message!=undefined || frm.doc.app_message!=undefined){
					console.log(frm.doc.email_message)
					console.log(frm.doc.sms_message)
					console.log(frm.doc.app_message)
				frappe.call({
					method: 'notification.notification.doctype.notification_tool.notification_tool.update_alert',
					args: {
						subject: frm.doc.subject,
						doctype: frm.doc.select_doctype,
						send_alert_on: frm.doc.send_alert_on,
						method: frm.doc.method,
						date_changed: frm.doc.date_changed,
						days_in_advance: frm.doc.days_in_advance,
						value_changed: frm.doc.value_changed,
						conditions: frm.doc.conditions,
						filters_json: frm.doc.filters_json,
						recipients: recipients,
						email_message: frm.doc.email_message,
						set_property_after_email: frm.doc.set_property_after_email,
						property_value_email: frm.doc.property_value_email,
						if_email_by_field: frm.doc.if_email_by_field,
						email_by_document_field: frm.doc.email_by_document_field,
						sms_message: frm.doc.sms_message,
						set_property_after_sms: frm.doc.set_property_after_sms,
						property_value_sms: frm.doc.property_value_sms,
						if_sms_by_field: frm.doc.if_sms_by_field,
						sms_by_document_field: frm.doc.sms_by_document_field,
						app_type: frm.doc.app_type,
						app_message: frm.doc.app_message,
						set_property_after_app: frm.doc.set_property_after_app,
						property_value_app: frm.doc.property_value_app,
						if_app_alert_by_field: frm.doc.if_app_alert_by_field,
						app_alert_by_document_field: frm.doc.app_alert_by_document_field
					},
					callback: function(r) {
						if(r.message){
							frappe.show_alert({message: __("Alert Created!"), indicator: 'green'});
							cur_frm.reload_doc();
						}
					}
				});
			}
			else{
				frappe.throw("Please Update atleast one of the following alert: <ul><li>Email Alert</li><li>SMS Alert</li><li>App Alert</li></ul>")
			}
			}
		});
	},
	if_email_by_field: function(frm){
		if(frm.doc.select_doctype){
			frm.trigger("alert_by_field")
		}
	},
	if_sms_by_field: function(frm){
		if(frm.doc.select_doctype){
			frm.trigger("alert_by_field")
		}
	},
	if_app_alert_by_field: function(frm){
		if(frm.doc.select_doctype){
			frm.trigger("alert_by_field")
		}
	},
	alert_by_field: function(frm){
		let get_select_options = function(df) {
			return {value: df.fieldname, label: df.fieldname + " (" + __(df.label) + ")"};
		}
		let get_date_change_options = function() {
			let date_options = $.map(fields, function(d) {
				return (d.fieldtype=="Date" || d.fieldtype=="Datetime")?
					get_select_options(d) : null;
			});
			// append creation and modified date to Date Change field
			return date_options.concat([
				{ value: "creation", label: `creation (${__('Created On')})` },
				{ value: "modified", label: `modified (${__('Last Modified Date')})` }
			]);
		}
		let fields = frappe.get_doc("DocType", frm.doc.select_doctype).fields;
		let options = $.map(fields,
			function(d) { return in_list(frappe.model.no_value_type, d.fieldtype) ?
				null : get_select_options(d); });
		
		frm.set_df_property("value_changed", "options", [""].concat(options));
		frm.set_df_property("set_property_after_email", "options", [""].concat(options));
		frm.set_df_property("set_property_after_sms", "options", [""].concat(options));
		frm.set_df_property("set_property_after_app", "options", [""].concat(options));
		

		// set date changed options
		frm.set_df_property("date_changed", "options", get_date_change_options());
		

		let email_fields = $.map(fields,
			function(d) { return (d.options == "Email" ||
				(d.options=='User' && d.fieldtype=='Link')) ?
				get_select_options(d) : null; });

		// set email recipient options
		cur_frm.fields_dict['email_by_document_field'].df.options= [""].concat(["owner"].concat(email_fields));
		
		
		let notification_fields = $.map(fields,
			function(d) { return (d.options == "DocType" || d.fieldtype=='Link') ?
				get_select_options(d) : null; });

		// set sms recipient options
		cur_frm.fields_dict['app_alert_by_document_field'].df.options= [""].concat(notification_fields);
		
			
		let phone_fields = $.map(fields,
			function(d) { return (d.options == "Phone" ||
				(d.options=='User' && d.fieldtype=='Link')) ?
				get_select_options(d) : null; });

		// set sms recipient options
		cur_frm.fields_dict['sms_by_document_field'].df.options= [""].concat(phone_fields);
		cur_frm.refresh_fields()
				
	},

	filters_fn: function(frm) {
		// sending default fieldname as name
		frm.events.show_filter(frm, 'name', '=', undefined, true, 0);
	},

	update_options: function(frm) {
		let doctype = frm.doc.select_doctype;
		let date_fields = [
			{ label: __('Created On'), value: 'creation' },
			{ label: __('Last Modified On'), value: 'modified' }
		];
		let value_fields = [];
		let update_form = function() {
			
			frm.trigger("show_filters");
		}


		if (doctype) {
			frappe.model.with_doctype(doctype, () => {
				// get all date and datetime fields
				frappe.get_meta(doctype).fields.map(df => {
					if (['Date', 'Datetime'].includes(df.fieldtype)) {
						date_fields.push({ label: df.label, value: df.fieldname });
					}
					if (['Int', 'Float', 'Currency', 'Percent'].includes(df.fieldtype)) {
						value_fields.push({ label: df.label, value: df.fieldname });
					}
				});
				update_form();
				frappe.meta.docfield_list[doctype] = frappe.get_meta(doctype).fields;
			});
		} else {
			// update select options
			update_form();
		}
	},

	show_filters: function(frm) {
		if(cur_frm.doc.filters_json=="[]" || cur_frm.doc.filters_json==undefined || cur_frm.doc.filters_json==""){
			frm.set_df_property("add_filter","hidden",0)
		}
		else{
			frm.set_df_property("add_filter","hidden",1)
		}
		if (frm.notification_filters && frm.notification_filters.length) {
			frm.trigger('render_filters_table');
		} else {
			
				// standard filters
				if (frm.doc.select_doctype) {
					// allow all link and select fields as filters
					frm.notification_filters = [];
					frappe.model.with_doctype(frm.doc.select_doctype, () => {
						frappe.get_meta(frm.doc.select_doctype).fields.map(df => {
							if (['Link', 'Select'].includes(df.fieldtype)) {
								let _df = copy_dict(df);

								// nothing is mandatory
								_df.reqd = 0;
								_df.default = null;
								_df.depends_on = null;
								_df.read_only = 0;
								_df.permlevel = 1;
								_df.hidden = 0;

								frm.notification_filters.push(_df);
							}
							frm.trigger('render_filters_table');
						});
					});
				}
		}
	},

	render_filters_table: function(frm) {
		frm.set_df_property("filters_section", "hidden", 0);
		// let fields = frm.notification_filters;

		let wrapper = $(frm.get_field('filters_json').wrapper).empty();
		let table = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
			<thead>
				<tr>
					<th style="width: 50%">${__('Filter')}</th>
					<th>${__('Condition')}</th>
					<th>${__('Value')}</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>`).appendTo(wrapper);

		let filters = JSON.parse(frm.doc.filters_json || '[]');
		var filters_set = false;

		if (filters) {
			filters.map((f, index) => {
				const filter_row = $(`<tr data-id="${index}"><td>${f[1]}</td><td>${f[2]}</td><td>${f[3]}</td></tr>`);
				table.find('tbody').append(filter_row);
				filters_set = true;
			});
		}

		if (!filters_set) {
			const filter_row = $(`<tr><td colspan="3" class="text-muted text-center">
				${__("No filters added")}</td></tr>`);
			table.find('tbody').append(filter_row);
		} else {
			$(`<p class="text-muted small">${__("Click on the row to edit filter")}</p>`).appendTo(wrapper);
		}

		table.find('tr').click(function() {
			let index = $(this).attr('data-id');
			if (filters[index]) {
				frm.events.show_filter(frm, filters[index][1], filters[index][2], filters[index][3], false, index);
			}
		});
	},

	add_filter: function(frm) {
		frm.trigger('filters_fn');
		
	},

	show_filter(frm, fieldname, condition, value, is_new, index) {

		let list_filter = new frappe.ui.Filter({
			parent: $(frm.get_field('filter_html').wrapper),
			parent_doctype: frm.doc.select_doctype,
			fieldname: fieldname,
			hidden: false,
			condition: condition,
			doctype: frm.doc.select_doctype,
			value: value,
			remove: function() {
				if (is_new == false) {
					// to delete filter from array
					let arr = JSON.parse(frm.doc.filters_json);
					arr.splice(parseInt(index), 1);
					frm.set_value('filters_json', JSON.stringify(arr));
					frm.trigger('show_filters');
				}
				this.filter_edit_area.remove();
			},
			on_change: function() {
				let val = list_filter.get_value();
				if (val[2] == 'like' || val[2] == 'Like')
					val[3] = val[3].replace(/%/g, "");
				let arr = JSON.parse(frm.doc.filters_json);
				if (is_new == false) {
					arr[index] = val;
				} else {
					arr.push(val);
				}
				frm.set_value('filters_json', JSON.stringify(arr));
				frm.trigger('show_filters');
			}
		});
		console.log(list_filter)
	}
});
