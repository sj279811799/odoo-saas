# -*- coding: utf-8 -*
""" 客户端初始化功能实现 """
import openerp
from openerp import models, api, SUPERUSER_ID


class ClientInstallAddons(models.Model):
    """ 安装模块类 """
    _name = 'client.install.addons'

    @api.model
    def _install_addons(self, client_env, addons):
        """ 调用模块的安装按钮 """
        for addon in client_env['ir.module.module'].search([('name', 'in', list(addons))]):
            addon.sudo().button_install()

    @api.model
    def registry(self, db_name, new=False, **kwargs):
        """ 根据db_name获取数据库实例 """
        m = openerp.modules.registry.RegistryManager
        if new:
            return m.new(db_name, **kwargs)
        else:
            return m.get(db_name, **kwargs)

    @api.model
    def update_registry(self, db_name):
        """ 刷新模块状态 """
        self.registry(db_name, new=True, update_module=True)

    @api.model
    def install_addons(self, addons, db_name):
        addons.append('auth_oauth')
        addons.append('saas_client')
        addons = set(addons)
        if not addons:
            return
        with self.registry(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, self._context)
            self._install_addons(env, addons)

    @api.model
    def set_endpoint(self, server_name, db_name):
        with self.registry(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, self._context)
            self._set_endpoint(env, server_name)

    @api.model
    def _set_endpoint(self, client_env, server_name):
        """ 设置oauth的endpoint """
        auth_endpoint = '%s/oauth2/auth' % server_name
        validation_endpoint = '%s/oauth2/tokeninfo' % server_name
        oauth_provider = client_env['auth.oauth.provider'].search([('name', '=', 'SaaS')], limit=1)
        if oauth_provider:
            oauth_provider.write({'auth_endpoint': auth_endpoint, 'validation_endpoint': validation_endpoint})