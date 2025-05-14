odoo.define('your_module.many2many_tags_click', function (require) {
    "use strict";
    var fieldRegistry = require('web.field_registry');
    var Many2ManyTags = require('web.relational_fields').FieldMany2ManyTags; // ✅ Extende TAGS

    var Many2ManyTagsClick = Many2ManyTags.extend({
        events: _.extend({}, Many2ManyTags.prototype.events, {
            'click .o_tag': '_onTagClick',
        }),
        _onTagClick: function (ev) {
            ev.preventDefault();
            var recordId = $(ev.currentTarget).data('id');
            if (recordId && this.field.relation) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: this.field.relation,
                    res_id: recordId,
                    views: [[false, 'form']],
                    target: 'current',
                });
            }
        },
    });
    fieldRegistry.add('many2many_tags_click', Many2ManyTagsClick);
});