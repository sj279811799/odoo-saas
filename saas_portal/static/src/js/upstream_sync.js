openerp.saas_portal.upstream_sync = function (instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.saas_portal = instance.web.saas_portal || {};

    instance.web.views.add('tree_upstream_line', 'instance.web.saas_portal.UpstreamView');
    instance.web.saas_portal.UpstreamView = instance.web.ListView.extend({
        init: function () {
            this._super.apply(this, arguments);
        },
        load_list: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.mod = new instance.web.DataSetSearch(this, 'saas.upstream');
            this.$el.prepend(QWeb.render("UpstreamSync", {widget: this}));
            this.$(".oe_upstream_sync").click(function () {
                self.mod.call("sync_upstream_list", [self.dataset.context]).then(function (result) {
                    self.do_action(result, {
                        clear_breadcrumbs: true
                    });
                })
            });
        },
    });
};