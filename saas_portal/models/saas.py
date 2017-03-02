# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import openerp.tools as tools
from rancher_util import Rancher
from dyupsapi import NginxClient
import requests
import werkzeug
import simplejson
import uuid

import logging
_logger = logging.getLogger(__name__)


class SaasRancherHost(models.Model):
    """ 主机 """
    _name = 'saas.rancher.host'

    host_id = fields.Char(string="Host ID")
    name = fields.Char(string="Name")
    host_name = fields.Char(string="Host Name")
    host_ip = fields.Char(string="Host IP")
    memory_total = fields.Char(string="Memory Total")
    memory_available = fields.Char(string="Memory Available")
    cpu = fields.Char(string="Cpu")
    cpu_count = fields.Char(string="Cpu Count")
    state = fields.Selection(selection=[('active', 'Active'), ('inactive', 'Inactive')], string='State')
    host_type = fields.Selection(selection=[('db', 'DB'), ('server', 'Server')], string="Host Type")

    @api.model
    def sync_host_list(self, context):
        """ 同步按钮js函数 """
        self.sync_host()
        action = self.env.ref('saas_portal.action_saas_rancher_host', False).read()[0]
        return action

    def sync_host(self):
        """ 同步rancher中的host """
        rancher_obj = self.env['saas.data.center']
        rancher = rancher_obj.search([('active', '=', True)], limit=1)
        if rancher:
            client = Rancher(rancher=rancher)
            host_lists = client.get_host()
            for rancher_host in host_lists:
                hrp_host_obj = self.env['saas.rancher.host']
                hrp_host = hrp_host_obj.search([('host_id', '=', rancher_host['host_id'])], limit=1)
                if hrp_host:
                    hrp_host.write(rancher_host)
                else:
                    hrp_host_obj.create(rancher_host)
        else:
            raise UserError(_("There is not have a valid rancher configuration!"))

    @api.multi
    def write(self, vals):
        rancher_obj = self.env['saas.data.center']
        res = super(SaasRancherHost, self).write(vals)
        if 'host_id' not in vals and 'host_type' in vals:
            rancher = rancher_obj.search([('active', '=', True)], limit=1)
            if rancher:
                client = Rancher(rancher=rancher)
                client.update_host_label(self.host_id, vals['host_type'])
            else:
                raise UserError(_("There is not have a valid rancher configuration!"))
        return res


class SaasDataCenter(models.Model):
    """ 数据中心 """
    _name = 'saas.data.center'

    name = fields.Char(string="Name")
    url = fields.Char(string="Url")
    env_name = fields.Char(string="Environment", default="Default")
    access_key = fields.Char(string="Access Key")
    secret_key = fields.Char(string="Secret Key")
    active = fields.Boolean(string="Active", hlep="Active", default=True)

    @api.multi
    def test_rancher_connection(self):
        """ 测试连接 """
        try:
            client = Rancher(rancher=self)
            if not client.get_env_id():
                raise UserError(_("Connection Test Failed! The environment is not exists!"))
        except Exception, e:
            raise UserError(_("Connection Test Failed! Here is what we got instead:\n %s") % tools.ustr(e))
        raise UserError(_("Connection Test Succeeded! Everything seems properly set up!"))


class SaasPartitionTemplate(models.Model):
    """ 分区模版 """
    _name = 'saas.partition.template'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    user_number = fields.Integer(string='User Number', default=0)
    active = fields.Boolean(string="Active", hlep="Active", default=True)
    docker_compose = fields.Text(string="Docker Compose")
    rancher_compose = fields.Text(string="Rancher Compose")


class SaasPartition(models.Model):
    """ 分区 """
    _name = 'saas.partition'

    partition_id = fields.Char()
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    code = fields.Char(string="Code", default='/')
    temp_id = fields.Many2one(comodel_name='saas.partition.template', string="Partition Template")
    user_number = fields.Integer(string="User Number", default=0)
    remainder = fields.Integer(compute="compute_remainder")
    line_ids = fields.One2many(comodel_name="saas.partition.line", inverse_name="partition_id",
                               compute="compute_line")
    port = fields.Char(string='Port', default='/')

    @api.model
    def create(self, vals):
        """ 创建分区和rancher分区 """
        rancher_obj = self.env['saas.data.center']
        template_obj = self.env['saas.partition.template']
        ir_sequence_obj = self.env['ir.sequence']
        res = super(SaasPartition, self).create(vals)
        if res.code == '/':
            partition_sequence = ir_sequence_obj.next_by_code('saas_partition')
            if not partition_sequence:
                raise UserError(_("Current company do not define SaaS Partition sequence,please contact the administrator."))
            res.code = partition_sequence
        if res.port == '/':
            port_sequence = ir_sequence_obj.next_by_code('saas_port')
            if not port_sequence:
                raise UserError(_("Current company do not define SaaS Port sequence,please contact the administrator."))
            res.port = port_sequence
        if vals:
            docker_compose = template_obj.browse(vals['temp_id']).docker_compose
            rancher_compose = template_obj.browse(vals['temp_id']).rancher_compose
            user_number = template_obj.browse(vals['temp_id']).user_number
            partition = {
                "description": vals['description'] if 'description' in vals else False,
                "name": res.code,
                "dockerCompose": docker_compose % (res.port, (user_number / 100)),
                "rancherCompose": rancher_compose,
                "startOnCreate": True,
            }
            rancher = rancher_obj.search([('active', '=', True)], limit=1)
            if rancher:
                client = Rancher(rancher=rancher)
                id = client.create_partition(partition)
                res.partition_id = id
            else:
                raise UserError(_("There is not have a valid rancher configuration!"))
        return res

    @api.depends('partition_id')
    def compute_line(self):
        rancher_obj = self.env['saas.data.center']
        partition_line_obj = self.env['saas.partition.line']
        rancher = rancher_obj.search([('active', '=', True)], limit=1)
        if rancher:
            client = Rancher(rancher=rancher)
            service_lists = client.get_service(self.partition_id)
            partition_lines = partition_line_obj
            for service in service_lists:
                partition_line = partition_line_obj.search([('partition_id', '=', self.id),
                                                            ('service_id', '=', service['service_id'])], limit=1)
                if partition_line:
                    partition_line.write(service)
                    partition_lines += partition_line
                else:
                    service['partition_id'] = self.id
                    partition_line = partition_line_obj.create(service)
                    partition_lines += partition_line
            self.line_ids = partition_lines
        else:
            raise UserError(_("There is not have a valid rancher configuration!"))

    @api.depends('user_number')
    def compute_remainder(self):
        for rec in self:
            rec.remainder = rec.temp_id.user_number - rec.user_number


class SaasPartitionLine(models.Model):
    """ 分区行:显示分区的Server """
    _name = 'saas.partition.line'

    partition_id = fields.Many2one(comodel_name="saas.partition")
    service_id = fields.Char()
    name = fields.Char(string="Name")
    state = fields.Selection(selection=[('active', 'Active'),
                                        ('inactive', 'Inactive'),
                                        ('activating', 'Activating'),
                                        ('registering', 'Registering')], string='State')
    kind = fields.Char(string="Kind")
    image = fields.Char(string="Image")
    scale = fields.Char(string="Scale")
    container_id = fields.Char(string="Container")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sub_domain = fields.Char(string="Sub Domain")
    admin_name = fields.Char(string="Admin Name")
    admin_password = fields.Char(string="Admin Password")
    user_number = fields.Char(string="User Number")

    def create_users(self, name, sub_domain, email, adminuser, password, package, template=False):
        schema_obj = self.env['saas.schema']
        package_obj = self.env['saas.package']
        res_partner_obj = self.env['res.partner']
        base_saas_domain = self.env['ir.config_parameter'].get_param("saas_portal.base_saas_domain")
        package = package_obj.search([('code', '=', package)])
        user_number = package.user_number

        # 创建用户
        user_vals = {
            'name': name,
            'company_type': 'company',
            'sub_domain': sub_domain,
            'website': '%s.%s' % (sub_domain, base_saas_domain),
            'user_number': user_number,
            'email': email,
            'admin_name': adminuser,
            'admin_password': password,
        }
        user = self.create(user_vals)

        # 创建客户
        schema_vals = {
            'name': sub_domain,
            'host': '%s.%s' % (sub_domain, base_saas_domain),
            'user_id': user.id,
            'user_number': user_number,
            'partition_id': False,
            'admin_name': adminuser,
            'admin_password': password,
            'client_id': str(uuid.uuid1()),
            'template': template,
        }
        schema_obj.create(schema_vals)

        # 发送admin邮件
        admin_user = self.env.ref('saas_portal.admin_mail')
        self.saas_send_mail(admin_user, admin=True)
        return True

    @api.model
    def saas_send_mail(self, user, admin=False):
        compose_message_obj = self.env['mail.compose.message']
        if admin:
            template = self.env.ref('saas_portal.mail_template_register_admin')
        else:
            template = self.env.ref('saas_portal.mail_template_customer_register')
        tmp_obj = {
            'model': 'res.partner',
            'partner_ids': [(6, 0, user.ids)],
            'res_id': user.id,
            'template_id': template.id,
            'composition_mode': 'comment',
            'body': template.body_html,
        }
        mail = compose_message_obj.create(tmp_obj)
        render_values = compose_message_obj.onchange_template_id(mail.template_id.id, mail.composition_mode,
                                                                 mail.model, user.id)['value']
        mail.body = render_values['body']
        mail.subject = render_values['subject']
        mail.partner_ids = user.ids
        mail.model = user._name
        mail.res_id = user.id
        mail.send_mail()


class SaasSchema(models.Model):
    """ 客户 """
    _name = 'saas.schema'
    _inherits = {'oauth.application': 'oauth_application_id'}

    name = fields.Char(string='Name')
    host = fields.Char(string='Host')
    is_template = fields.Boolean(string='Is Template', default=False)
    user_id = fields.Many2one(comodel_name='res.partner', string="User")
    user_number = fields.Integer(string='User Number')
    admin_name = fields.Char(string="Admin Name")
    admin_password = fields.Char(string="Admin Password")
    partition_id = fields.Many2one(comodel_name="saas.partition", string="Partition")
    users_len = fields.Integer(string='Count users', readonly=True)
    file_storage = fields.Integer(string='File storage (MB)', readonly=True)
    db_storage = fields.Integer(string='DB storage (MB)', readonly=True)
    client_id = fields.Char(string='Database UUID', readonly=True, select=True)
    oauth_application_id = fields.Many2one(comodel_name='oauth.application', string='OAuth Application', ondelete='cascade')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('confirm', 'Confirm'),
                                        ('done', 'Done'),
                                        ('close', 'Close')],
                             string='State', default='draft')
    template = fields.Char(string='Template', readonly=True)

    @api.one
    def _request_params(self, path='/web', scheme=None, port=None, state={}, scope=None, client_id=None):
        scheme = scheme or 'http'
        port = port or '80'
        scope = scope or ['userinfo', 'force_login', 'trial', 'skiptheuse']
        client_id = client_id or str(uuid.uuid1())
        scope = ' '.join(scope)
        params = {
            'scope': scope,
            'state': simplejson.dumps(state),
            'redirect_uri': '{scheme}://{saas_server}:{port}{path}'.format(scheme=scheme, port=port,
                                                                           saas_server=self.host, path=path),
            'response_type': 'token',
            'client_id': client_id,
        }
        return params

    @api.one
    def _request(self, **kwargs):
        params = self._request_params(**kwargs)[0]
        url = '/oauth2/auth?%s' % werkzeug.url_encode(params)
        return url

    @api.multi
    def _request_url(self, path):
        r = self[0]
        state = {
            'd': r.name,
            'host': r.host,
            'client_id': r.client_id,
        }
        url = r._request(path=path, state=state)
        return url

    @api.multi
    def action_redirect_to_server(self):
        url = self._request_url('/saas_client/oauth_login')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'name': 'Redirection',
            'url': url
        }

    @api.multi
    def _request_server(self, path=None, scheme=None, port=None, **kwargs):
        nginx_obj = self.env['saas.nginx']
        ups_url = nginx_obj.search([('active', '=', True)], limit=1).url.split(':')[0]
        params = self._request_params(**kwargs)[0]
        access_token = self.oauth_application_id.sudo()._get_access_token(create=True)
        params.update({
            'token_type': 'Bearer',
            'access_token': access_token,
            'expires_in': 3600,
        })
        url = 'http://{host}:{port}{path}'.format(scheme=scheme, host=ups_url, port=8080, path=path)
        req = requests.Request('GET', url, data=params, headers={'host': self.host})
        req_kwargs = {'verify': True}
        return req.prepare(), req_kwargs

    @api.one
    def action_sync_client(self):
        state = {
            'd': self.name,
            'client_id': self.client_id,
        }
        req, req_kwargs = self._request_server(path='/saas_client/sync_server', state=state, client_id=self.client_id)
        res = requests.Session().send(req, **req_kwargs)

        if not res.ok:
            raise Warning('Reason: %s \n Message: %s' % (res.reason, res.content))
        try:
            data = simplejson.loads(res.text)
        except:
            _logger.error('Error on parsing response: %s\n%s' % ([req.url, req.headers, req.body], res.text))
            raise
        self.write(data)
        return None

    @api.one
    def _request_paramsc(self, path='/web', scheme=None, port=None, state={}, scope=None, client_id=None):
        scheme = scheme or 'http'
        port = port or '80'
        scope = scope or ['userinfo', 'force_login', 'trial', 'skiptheuse']
        client_id = client_id or str(uuid.uuid1())
        scope = ' '.join(scope)
        params = {
            'scope': scope,
            'state': simplejson.dumps(state),
            'redirect_uri': '{scheme}://{saas_server}:{port}{path}'.format(scheme=scheme, port=port,
                                                                           saas_server=self.host, path=path),
            'client_id': client_id,
        }
        return params

    @api.multi
    def _request_serverc(self, path=None, scheme=None, port=None, **kwargs):
        nginx_obj = self.env['saas.nginx']
        ups_url = nginx_obj.search([('active', '=', True)], limit=1).url.split(':')[0]
        params = self._request_paramsc(**kwargs)[0]
        url = 'http://{host}:{port}{path}'.format(scheme=scheme, host=ups_url, port=8080, path=path)
        req = requests.Request('GET', url, data=params, headers={'host': self.host})
        req_kwargs = {'verify': True}
        return req.prepare(), req_kwargs

    @api.one
    def install_addons(self):
        partner_obj = self.env['res.partner']
        for rec in self:
            state = {
                'd': rec.name,
                'client_id': rec.client_id,
                'addons': [],
            }
            req, req_kwargs = self._request_serverc(path='/client_init/install_addons', state=state, client_id=rec.client_id)
            res = requests.Session().send(req, **req_kwargs)
            rec.write({
                'state': 'done',
            })
            partner_obj.saas_send_mail(rec.user_id)

    @api.model
    def create(self, vals):
        self = super(SaasSchema, self).create(vals)
        self.oauth_application_id._get_access_token(create=True)
        return self

    @api.model
    def delete_db(self):
        nginx_obj = self.env['saas.nginx']
        base_saas_domain = self.env['ir.config_parameter'].get_param("saas_portal.base_saas_domain")
        host = '%s.%s' % (self.name, base_saas_domain)
        ups_url = nginx_obj.search([('active', '=', True)], limit=1).url.split(':')[0]
        url = '{scheme}://{host}:{port}{path}'.format(scheme='http', host=ups_url, port=8080, path='/web/database/saas_drop')
        data = {'name': self.name,
                'master_pwd': self.admin_password}
        req = requests.Request('POST', url, data=data, headers={'host': host})
        req_kwargs = {'verify': True}
        res = requests.Session().send(req.prepare(), **req_kwargs)
        return res

    @api.multi
    def unlink(self):
        schema_obj = self.env['saas.schema']
        upstream_obj = self.env['saas.upstream']
        for rec in self:
            if schema_obj.search([('template', '=', rec.name), ('state', '=', 'draft')]):
                raise ValidationError(_('There also exist draft schema reference this schema template.'))
            # 删除db
            rec.delete_db()
            # 删除user
            rec.user_id.unlink()
            # 恢复分区使用数量
            user_number = rec.partition_id.user_number - float(rec.user_number)
            rec.partition_id.write({
                'user_number': user_number,
            })
            # 删除nginx
            upstream_obj.search([('host_name', '=', rec.host)], limit=1).unlink()
        # 删除客户
        return super(SaasSchema, self).unlink()

    @api.multi
    def action_confirm(self):
        partition_obj = self.env['saas.partition']
        partner_obj = self.env['res.partner']
        nginx_obj = self.env['saas.nginx']
        server_obj = self.env['saas.server']
        rancher_obj = self.env['saas.data.center']
        for rec in self:
            use_partition = self.get_partition(rec.user_number)
            if not use_partition:
                template = self.get_template(rec.user_number)
                if not template:
                    raise ValidationError(_('Can not find the appropriate partition template,please contact the administrator.'))
                use_partition = partition_obj.create({
                    'name': rec.name,
                    'description': 'automatically create for' + rec.name,
                    'temp_id': template.id,
                })
            # 创建upstream
            lb_ip =False
            rancher = rancher_obj.search([('active', '=', True)], limit=1)
            if rancher:
                client = Rancher(rancher=rancher)
                container_id = client.get_container_id(use_partition.partition_id)
                lb_ip = client.get_lb_ip(container_id)
            else:
                raise UserError(_("There is not have a valid rancher configuration!"))

            nginx = nginx_obj.search([('active', '=', True)], limit=1)
            if nginx:
                url = 'http://%s/upstream/%s' % (nginx.url, rec.host)
                data = 'server %s:%s;' % (lb_ip, use_partition.port)
                nginx_obj = NginxClient()
                services = nginx_obj._post(url, data=data)
                server_obj.create({
                    'host_name':rec.host,
                })
            else:
                raise UserError(_("There is not have a valid nginx configuration!"))
            # 创建或复制数据库
            if rec.template:
                self.duplicate_db(rec.template, rec.name, rec.admin_password)
                partner_obj.saas_send_mail(rec.user_id)
                state = 'done'
            else:
                self.create_db(rec.name, rec.admin_name, rec.admin_password)
                state = 'confirm'
            use_partition.write({
                'user_number': rec.user_number + use_partition.user_number,
            })
            rec.write({
                'partition_id': use_partition.id,
                'state': state,
            })

    def get_partition(self, user_number):
        partition_obj = self.env['saas.partition']
        partitions = partition_obj.search([('remainder', '>', 0)])
        sort_partitions = sorted(partitions, key=lambda p: p.remainder, reverse=False)
        for partition in sort_partitions:
            if partition.remainder >= user_number:
                return partition
        return False

    def get_template(self, user_number):
        template_obj = self.env['saas.partition.template']
        templates = template_obj.search([('user_number', '>=', user_number)])
        sort_templates = sorted(templates, key=lambda t: t.user_number, reverse=False)
        for template in sort_templates:
            if template.user_number >= user_number:
                return template
        return False

    def create_db(self, sub_domain, adminuser, password):
        nginx_obj = self.env['saas.nginx']
        base_saas_domain = self.env['ir.config_parameter'].get_param("saas_portal.base_saas_domain")
        host = '%s.%s' % (sub_domain, base_saas_domain)
        ups_url = nginx_obj.search([('active', '=', True)], limit=1).url.split(':')[0]
        url = '{scheme}://{host}:{port}{path}'.format(scheme='http', host=ups_url, port=8080, path='/web/database/saas_create')
        data = {'name': sub_domain,
                'lang': 'zh_CN',
                'master_pwd': password,
                'password': password,
                'login': adminuser}
        req = requests.Request('POST', url, data=data, headers={'host': host})
        req_kwargs = {'verify': True}
        res = requests.Session().send(req.prepare(), **req_kwargs)
        return res

    def duplicate_db(self, name, new_name, master_pwd):
        nginx_obj = self.env['saas.nginx']
        base_saas_domain = self.env['ir.config_parameter'].get_param("saas_portal.base_saas_domain")
        host = '%s.%s' % (new_name, base_saas_domain)
        ups_url = nginx_obj.search([('active', '=', True)], limit=1).url.split(':')[0]
        url = '{scheme}://{host}:{port}{path}'.format(scheme='http', host=ups_url, port=8080, path='/web/database/saas_duplicate')
        data = {'master_pwd': master_pwd,
                'name': name,
                'new_name': new_name}
        req = requests.Request('POST', url, data=data, headers={'host': host})
        req_kwargs = {'verify': True}
        res = requests.Session().send(req.prepare(), **req_kwargs)
        return res


class SaasPackage(models.Model):
    """ 套餐设置 """
    _name = 'saas.package'

    name = fields.Char(string='Name')
    user_number = fields.Integer(string='User Number')
    price = fields.Char(string="Price")
    code = fields.Char()