/** @odoo-module **/
import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
import { patch } from "@web/core/utils/patch";
const { onMounted, useEffect } = owl;
patch(ProgressBarField.prototype, 'prgress_bar_custom',{
   setup(v){
       var value = this.props.value;
       console.log(this)
       this._super(...arguments)
       useEffect(() => this._render_value());
   },
   _render_value: function (v) {
       var value = this.props.value;
       var max_value = this.state.maxValue;
       if (!isNaN(v)) {
           if (this.edit_max_value) {
               max_value = v;
           } else {
               value = v;
           }
       }
       value = value || 0;
       max_value = max_value || 0;
       var widthComplete;
       if (value <= max_value) {
           widthComplete = value/max_value * 100;
       } else {
           widthComplete = 100;
       }
       $('.o_progress').toggleClass('o_progress_overflow', value > max_value)
           .attr('aria-valuemin', '0')
           .attr('aria-valuemax', max_value)
           .attr('aria-valuenow', value);
           $('.o_progressbar_complete').toggleClass('o_progress_red', widthComplete > 101).css('width', widthComplete + '%');
           $('.o_progressbar_complete').toggleClass('o_progress_yellow', widthComplete > 75 && widthComplete <= 100).css('width', widthComplete + '%');
           $('.o_progressbar_complete').toggleClass('o_progress_light_green', widthComplete > 41 && widthComplete <= 74).css('width', widthComplete + '%');
           $('.o_progressbar_complete').toggleClass('o_progress_green', widthComplete > 0 && widthComplete <= 40).css('width', widthComplete + '%');
   },
})