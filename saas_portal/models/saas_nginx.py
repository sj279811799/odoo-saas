# -*- coding: utf-8 -*-
""" nginx配置 """
from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import openerp.tools as tools
from dyupsapi import NginxClient


class SaasUpstream(models.Model):
    """ Upstream """
    _name = 'saas.upstream'
    _rec_name = 'host_name'

    host_name = fields.Char(string="Host Name", readonly=1)
    server_ids = fields.One2many(comodel_name='saas.server', inverse_name="upstream_id", compute="compute_line")

    @api.depends('host_name')
    def compute_line(self):
        nginx_obj = self.env['saas.nginx']
        server_obj = self.env['saas.server']
        nginx = nginx_obj.search([('active', '=', True)], limit=1)
        if nginx:
            url = 'http://%s/upstream/%s' % (nginx.url, self.host_name)
            nginx = NginxClient()
            services = nginx._get(url)
            if services:
                service_lists = services.splitlines()
                server_lines = server_obj
                for service in service_lists:
                    server_line = server_obj.search([('upstream_id', '=', self.id),
                                                     ('ip_port', '=', service)], limit=1)
                    if server_line:
                        server_lines += server_line
                    else:
                        vals = {
                            'upstream_id': self.id,
                            'ip_port': service,
                        }
                        server_line = server_obj.create(vals)
                        server_lines += server_line
            else:
                server_lines = False
            self.server_ids = server_lines
        else:
            raise UserError(_("There is not have a valid nginx configuration!"))

    @api.model
    def sync_upstream_list(self, context):
        self.sync_upstream()
        action = self.env.ref('saas_portal.action_saas_upstream', False).read()[0]
        return action

    def sync_upstream(self):
        nginx_obj = self.env['saas.nginx']
        nginx = nginx_obj.search([('active', '=', True)], limit=1)
        if nginx:
            url = 'http://%s/list' % nginx.url
            nginx = NginxClient()
            upstream_lists = nginx._get(url).splitlines()
            for upstream in upstream_lists:
                upstream_obj = self.env['saas.upstream']
                hrp_upstream = upstream_obj.search([('host_name', '=', upstream)], limit=1)
                if not hrp_upstream:
                    upstream_obj.create({
                        'host_name':upstream,
                    })
        else:
            raise UserError(_("There is not have a valid rancher configuration!"))

    @api.multi
    def unlink(self):
        for rec in self:
            nginx_obj = self.env['saas.nginx']
            nginx = nginx_obj.search([('active', '=', True)], limit=1)
            if nginx:
                url = 'http://%s/upstream/%s' % (nginx.url, rec.host_name)
                nginx = NginxClient()
                result = nginx._delete(url)
                print result
            else:
                raise UserError(_("There is not have a valid rancher configuration!"))
        return super(SaasUpstream, self).unlink()


class SaasServer(models.Model):
    """ Nginx Server """
    _name = 'saas.server'

    ip_port = fields.Char(string='Ip', readonly=1)
    weight = fields.Char(string='Weight', default='1')
    max_fails = fields.Char(string='Max Fails', default='1')
    fail_timeout = fields.Char(string='Fail Timeout', default='10')
    backup = fields.Char(string='Backup', default='0')
    down = fields.Char(string='Down', default='0')
    upstream_id = fields.Many2one(comodel_name='saas.upstream')


class SaasNginx(models.Model):
    """ Nginx连接配置 """
    _name = 'saas.nginx'

    name = fields.Char(string="Name")
    url = fields.Char(string="Url")
    active = fields.Boolean(string="Active", hlep="Active", default=True)

    @api.multi
    def test_nginx_connection(self):
        """ 连接测试 """
        url = 'http://%s/detail' % self.url
        try:
            nginx = NginxClient()
            nginx._get(url)
        except Exception, e:
            raise UserError(_("Connection Test Failed! Here is what we got instead:\n %s") % tools.ustr(e))
        raise UserError(_("Connection Test Succeeded! Everything seems properly set up!"))