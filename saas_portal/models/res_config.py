from openerp import models, fields, api


class BaseConfigSettings(models.TransientModel):
    """ 域名设置 """
    _inherit = 'base.config.settings'

    base_saas_domain = fields.Char(string='Base SaaS domain')

    def get_default_base_saas_domain(self, cr, uid, ids, context=None):
        base_saas_domain = self.pool.get("ir.config_parameter").get_param(cr, uid, "saas_portal.base_saas_domain", default=None, context=context)
        return {'base_saas_domain': base_saas_domain or False}

    def set_base_saas_domain(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for record in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, "saas_portal.base_saas_domain", record.base_saas_domain or '', context=context)