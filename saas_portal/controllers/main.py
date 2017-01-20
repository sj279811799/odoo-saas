# -*- coding: utf-8 -*

from openerp.addons.web.controllers.main import Home
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)


class SaasHome(Home):
    """ 处理web请求 """

    @http.route('/web/customer_register', type='http', auth="none")
    def web_customer_register(self, req, redirect=None, **kw):
        """ 处理用户注册请求 """
        res_partner_obj = req.env['res.partner']
        schema_obj = req.env['saas.schema']
        package_obj = req.env['saas.package']
        vals = [' ']
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            if schema_obj.sudo().search_count([('name', '=', request.params['subdomain'])]) > 0:
                values['error'] = _("Sub Domain already exist!")
            elif res_partner_obj.sudo().search_count([('name', '=', request.params['name'])]) > 0:
                values['error'] = _("Name already exist!")
            else:
                if 'select' in request.params and request.params['select'] != ' ':
                    template = request.params['select']
                else:
                    template = False
                res_partner_obj.sudo().create_users(request.params['name'], request.params['subdomain'],
                                                    request.params['email'], request.params['adminuser'],
                                                    request.params['password'], request.params['package'],
                                                    template=template)
                values['message'] = _('Register Success!We will send email to you when the database is ready.')
        schemas = schema_obj.sudo().search([('is_template', '=', True)])
        for schema in schemas:
            vals.append(schema.name)
        values['template'] = vals
        packages = package_obj.sudo().search([])
        for package in packages:
            values[package.code] = package.user_number
        return request.render('web.customer_register', values)
