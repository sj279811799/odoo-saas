openerp.saas_portal.rancher_list_sync = function (instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.saas_portal = instance.web.saas_portal || {};

    instance.web.views.add('tree_rancher_host_line', 'instance.web.saas_portal.HostSyncListView');
    instance.web.saas_portal.HostSyncListView = instance.web.ListView.extend({
        init: function () {
            this._super.apply(this, arguments);
        },
        load_list: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.mod = new instance.web.DataSetSearch(this, 'saas.rancher.host');
            this.$el.prepend(QWeb.render("RancherHostSync", {widget: this}));
            this.$(".oe_rancher_host_sync").click(function () {
                self.mod.call("sync_host_list", [self.dataset.context]).then(function (result) {
                    self.do_action(result, {
                        clear_breadcrumbs: true
                    });
                })
            });
        },
    });
};