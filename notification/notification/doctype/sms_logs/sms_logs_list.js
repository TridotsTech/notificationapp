frappe.listview_settings['SMS Logs'] = {
    add_fields: ["sender_name", "sent_on", "no_of_requested_sms", "from_sms"],
    // filters: [["from_sms", "=", "SMS Center"]],
    refresh: function(doclist) {
        
    },
    onload: function (listview) {
        frappe.route_options = {"from_sms": ["=", "SMS Center"]};
    }
}