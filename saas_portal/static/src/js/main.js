openerp.saas_portal = function (instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    openerp.saas_portal.rancher_list_sync(instance, local);
    openerp.saas_portal.upstream_sync(instance, local);
};