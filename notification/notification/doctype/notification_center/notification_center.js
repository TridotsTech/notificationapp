// Copyright (c) 2018, Tridots Tech and contributors
// For license information, please see license.txt
var valuesDocss = [];
frappe.require('assets/frappe/js/frappe/ui/filters/filter.js');
frappe.ui.form.on('Notification Center', {
    refresh: function(frm) {
        // if(!cur_frm.doc.filters_json){
        //     frm.set_value('filters_json', '[]');
        // }
        // $('button[data-fieldname="add_filter"]').addClass('btn-primary');
        // frm.fields_dict["add_filter"].$input.addClass('btn-primary');
        // if(frm.doc.send_to){
        //     frm.trigger('update_options');    
        // }
        // frm.ref_filters = null;
        // let wrapper = $(frm.get_field('filter_html').wrapper).empty();
        // wrapper.append('<div class="filter-edit-area"></div>');

        cur_frm.set_value('app_type', 'User App');
        if(frm.doc.send_to == "Drivers"){
            cur_frm.set_value('app_type', 'Driver App');
        }
        if(frm.doc.send_to == "Business"){
            cur_frm.set_value('app_type', 'Admin App');
        }
        if(frm.doc.send_to == "Customers"){
            cur_frm.set_value('app_type', 'User App');
        }
        frm.set_query("send_to", function() {
            return{
                "filters": {
                    "name": ["in", ["Customers","Drivers","Employee"]]
                }
            }
        });
        cur_frm.disable_save()
        frappe.breadcrumbs.add("Setup");
        cur_frm.set_df_property('items','hidden',1);
        cur_frm.set_value('url', 'General');
        cur_frm.set_value('message', '');
        cur_frm.set_value('send_to', '');
        cur_frm.set_value('content_data', '');
        cur_frm.set_value('party_list', '');
        cur_frm.set_value('receiver_list', '');
        frm.set_value({'redirect_document': '', 'redirect_doc': ''});
        frm._redirect_url = null;
        frm.set_query('redirect_document', function() {
            return {
                'filters': {
                    'name': ['in', ['Product', 'Product Category', 'Product Brand', 'Web Page Builder']]
                }
            }
        })
         // frm.set_df_property("filters_json", "hidden", 1);

        if(!cur_frm.doc.filters_json){
            frm.set_value('filters_json', '[]');
        }
       // frm.trigger('update_options');
        $('button[data-fieldname="add_filter"]').addClass('btn-primary');
        frm.fields_dict["add_filter"].$input.addClass('btn-primary');
        
        if(frm.doc.send_to){
           
            frm.set_df_property("add_filter", "hidden", 0);
            frm.trigger('update_options');    
            frm.set_df_property("filters_json", "hidden", 0);
        }
        else{
           
            frm.set_df_property("add_filter", "hidden", 1);
            frm.set_df_property("filters_json", "hidden", 1);
        }
        frm.notification_filters = null;
        frm.child_notification_filters = null;
        let wrapper = $(frm.get_field('filter_html').wrapper).empty();
        wrapper.append('<div class="filter-edit-area"></div>');


    },
    // send_to: function(frm){
	   
    // },
    create_receiver_list: function(frm) {

    },
    send_to: function(frm){
         cur_frm.set_value('url', 'General');
        if(frm.doc.send_to){
            frm.set_value('filters_json', '[]');
            frm.trigger('update_options');
            frm.set_df_property("add_filter", "hidden", 0);
            frm.set_df_property("filters_json", "hidden", 0);
        }else{
            frm.set_df_property("filters_json", "hidden", 1);
        }
    },
    filters_fn: function(frm) {
        // sending default fieldname as name
        frm.events.show_filter(frm, 'name', '=', undefined, true, 0);
    },
    update_options: function(frm) {
        let doctype = frm.doc.send_to;
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
                    if(df){
                        if (['Date', 'Datetime'].includes(df.fieldtype)) {
                            date_fields.push({ label: df.label, value: df.fieldname });
                        }
                        if (['Int', 'Float', 'Currency', 'Percent'].includes(df.fieldtype)) {
                            value_fields.push({ label: df.label, value: df.fieldname });
                        }
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
        if (frm.notification_filters && frm.notification_filters.length) {
            frm.trigger('render_filters_table');
        } else {
                // standard filters
                if (frm.doc.send_to) {
                    
                    // allow all link and select fields as filters
                    frm.notification_filters = [];
                    frappe.model.with_doctype(frm.doc.send_to, () => {
                        frappe.get_meta(frm.doc.send_to).fields.map(df => {
                           
                            if(df){
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
                            }

                            frm.trigger('render_filters_table');
                        });
                    });
                }
        }
    },

    render_filters_table: function(frm) {
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
            parent_doctype: frm.doc.send_to,
            fieldname: fieldname,
            hidden: false,
            condition: condition,
            doctype: frm.doc.send_to,
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
    },
    after_save: function(frm){
	    cur_frm.reload_doc();
    },
    get_list: function(frm) {
	    
        if(!frm.doc.send_to){
            frappe.msgprint('Please select send to');
        }else{
            valuesDocss = [];
             frappe.call({
                method: "notification.notification.doctype.notification_center.notification_center.get_device_ids",
                args: {
                    "party_type" : frm.doc.send_to,
                    "filters_json": frm.doc.filters_json
                },
                callback: function(r) {
                    console.log(r)
                    if (r.message) {
                        var a = '';
                        var b = '';
                        for (var i = 0; i < r.message.length; i++) {
                            a += r.message[i].device_id + '\n';
                            frm.set_value('receiver_list', a);
                        }
                        for (var i = 0; i < r.message.length; i++) {
                            b += r.message[i].name + '\n';
                            frm.set_value('party_list', b);
                        }
                        for (var i = 0; i < r.message.length; i++) {
                            var memberdata = {
                                member: r.message[i].name,
                                user_type:frm.doc.send_to
                                // member_name: r.message[i].member_name
                            }
                            valuesDocss.push(memberdata);
                        }
                    }

                }
            });
        }
    },

    send_notification: function(frm) {
      send(frm);
        // if (frm.doc.url != 'General') {
        //     if (frm.doc.items != '' && frm.doc.items != undefined) {
        //         send(frm)
        //     } else {
        //         frappe.msgprint('Please select Redirect Url')
        //     }
        // } else {
        //     send(frm)
        // }
    },
    redirect_doc: function(frm) {
        if(frm.doc.redirect_document && frm.doc.redirect_doc) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': frm.doc.redirect_document,
                    'fieldname': 'route',
                    'filters': {'name': frm.doc.redirect_doc}
                },
                callback: function(r) {
                    if(r.message) {
                        frm._redirect_url = r.message.route;
                    }
                }
            })
        } else {
            frm._redirect_url = null;
        }
    }
});
var send = function(frm) {
    var a = frm.doc.receiver_list.split("\n");
    var b = a.filter(function(v) { return v !== '' });
    // frappe.call({
    //     method: "notification.notification.doctype.app_alert_settings.app_alert_settings.send_app_notification",
    //     args: {
    //        "reference_doc":"User",
    //        "name":frm.doc.content_data,
    //        "player_ids": b,
    //        "subject":frm.doc.message,
    //        "reciever_type":reciever_type,
    //        "condition":frm.doc.message
    //     },
    //     callback: function(r) {
    //         console.log(r)
    //         frappe.msgprint('Notification Sent Successfully');
    //         cur_frm.set_value('party_list', null);
    //         cur_frm.set_value('message', null);
    //         cur_frm.set_value('content_data', "");
    //         cur_frm.set_value('url', 'General')
    //         cur_frm.set_value('items', null);
    //     }
    // })

    // frappe.call({
    //     "method": "frappe.client.get",
    //     args: {
    //         doctype: "App Alert Settings",
    //     },
    //     callback: function(r) {
        frappe.call({
                    method: "notification.notification.doctype.notification_center.notification_center.get_settings",
                    callback: function(r) {
            if(r.message){
		console.log(r.message)
		if(!frm.doc.content_data){
			frappe.throw('Please fill subject');
		}
		if(!frm.doc.message){
			frappe.throw('Please fill Message');
		}
        if(!frm.doc.receiver_list){
            frappe.throw('No receipient selected.');
        }
		if (frm.doc.content_data && frm.doc.message && frm.doc.receiver_list){
		        $.each(r.message.keys, function(i,k){
		           if(k.app_type == frm.doc.app_type){
		                var receiver = frm.doc.receiver_list.split("\n");
		                var one_signal_userconfig = {
		                    headers: {
		                        'Content-Type': 'application/json',
		                        "Authorization": "Basic " + k.secret_key
		                    }
		                };
		                var info = {};
		                var user_notification_data = {
		                    "app_id": k.app_id,
		                    "headings": { "en": frm.doc.content_data, },
		                    "contents": { "en": frm.doc.message, },
		                    "data": { "add_data": frm.doc.message, 'url': frm._redirect_url },
		                    "include_player_ids": b
		                }
                let is_url = 0
                // if(frappe.sys_defaults.installed_apps.includes("frappe_s3_attachment")){
				// frappe.model.get_value('S3 File Attachment', {'name': 'S3 File Attachment'}, ['end_point_url', 'cdn_url'], function(d) {
				// 	if(d.end_point_url){
				// 		is_url=1
				// 	}
				// 	if(d.cdn_url){
				// 		is_url=1
				// 	}
                //     })
                // }
					let base=""
					if(is_url==0){
						base = window.location.origin+"/"
					}
				        if (frm.doc.attach_image){                            
				            //user_notification_data['big_picture']=window.location.origin+"/"+frm.doc.attach_image
						user_notification_data['big_picture']=base+frm.doc.attach_image
				        }
				        if (cur_frm.doc.large_icon){
				            //user_notification_data['large_icon']=window.location.origin+"/"+cur_frm.doc.large_icon
						user_notification_data['large_icon']=base+cur_frm.doc.large_icon
				        }
				        if (cur_frm.doc.small_icon){            
				            //user_notification_data['small_icon']=window.location.origin+"/"+cur_frm.doc.small_icon
						user_notification_data['small_icon']=base+cur_frm.doc.small_icon
				        }
					console.log("----------user_notification_data--------------")
				        console.log(user_notification_data)
				        $.post(r.message.notification_gateway_url, user_notification_data, one_signal_userconfig).done(function(e) { console.log(e); });
					
				
		           }
		        })
		        
		        frappe.call({
		            method: "notification.notification.doctype.notification_center.notification_center.insert_notification",
		            args: {
		                name: frm.doc.content_data,
		                message: frm.doc.message,
		                device_ids: JSON.stringify(b),
		                table_5: valuesDocss,
		                reciever_type: frm.doc.app_type
		            },
		            callback: function(Responseresult) {
				
				frappe.call({
				    method: "notification.notification.doctype.notification_center.notification_center.delete_attached_images",
				    args: {
				        attach_image: frm.doc.attach_image,
				        large_icon: frm.doc.large_icon,
				        small_icon: frm.doc.small_icon
				    },
				    async:false,
				    callback: function(r) {
			
					}
				})
				frappe.msgprint('Notification Sent Successfully');
                cur_frm.set_value('party_list', null);
                cur_frm.set_value('message', null);
                cur_frm.set_value('content_data', "");
                cur_frm.set_value('url', null);
                cur_frm.set_value('items', null);
                cur_frm.set_value('attach_image', "");
                cur_frm.set_value('large_icon', "");
                cur_frm.set_value('small_icon', "");
                cur_frm.set_value({'redirect_document': '', 'redirect_doc': ''});
                cur_frm._redirect_url = null;
				cur_frm.save();
				
		            }
		        });
		}
            }
        }
    });
}
// frappe.ui.form.on("App Notification Center", "refresh", function(frm) {
//     cur_frm.set_query("items", function(s) {
//         // frappe.call({
//         //     method: "frappe.client.get_list",
//         //     args: {
//         //         doctype: frm.doc.events,
//         //         fields: ['name']

//         //     },
//         //     callback: function(r) {
//         //         if (r.message) {
//         //             frm.set_value(r.message)
//         //             // var a = '';
//         //             // var b = '';
//         //             // for (var i = 0; i < r.message.length; i++) {
//         //             //     a += r.message[i].player_id + '\n';
//         //             //     frm.set_value('events', a)
//         //             // }
//         //             // for (var i = 0; i < r.message.length; i++) {
//         //             //     b +=r.message[i].name +' - '+ r.message[i].member_name + '\n';
//         //             //     frm.set_value('member_list', b)
//         //             // }
//         //         }
//         //     }
//         // });
//         return {
//             "filters": {
//                 "sponsorship_type": (frm.doc.url)
//             }
//         };
//     });
// });
frappe.ui.form.on('Notification Center', 'url', function(frm, cdt, cdn) {
    if (frm.doc.url) {
        frappe.call({
            method: 'notification.notification.doctype.notification_center.notification_center.get_items',
            args: {
                url: frm.doc.url
            },
            callback: function(data) {
                var html = '';
                if (data.message == undefined) {
                    $('select[data-fieldname=items]').html(html)
                    $('select[data-fieldname=items]').parent().parent().parent().parent().hide()
                } else if (data.message.length > 0) {
                    html = '<option></option>'
                    if (frm.doc.sponsorship_type == 'Samaj Darshan') {
                        for (var i = 0; i < data.message.length; i++) {
                            var list = data.message[i].list;
                            for (var j = 0; j < list.length; j++) {
                                var value = list[j].month + '-' + data.message[i].year;
                                html += '<option value="' + value + '">' + value + '</option>';
                            }
                        }
                    } else {
                        for (var i = 0; i < data.message.length; i++) {
                            html += '<option value="' + data.message[i].name + '">' + data.message[i].name + '</option>';
                        }
                    }

                    $('select[data-fieldname=items]').html(html)
                    $('select[data-fieldname=items]').parent().parent().parent().parent().show()
                } else {
                    $('select[data-fieldname=items]').parent().parent().parent().parent().hide()
                }
            }
        })
    }
})
