# -*- coding: utf-8 -*-
""" 接收Portal端各种请求 """
from openerp import http
from openerp.http import request
from openerp import api, SUPERUSER_ID
from openerp.addons.auth_oauth.controllers.main import fragment_to_query_string
import functools
import simplejson
import werkzeug.utils
import logging

_logger = logging.getLogger(__name__)


def webservice(f):
    @functools.wraps(f)
    def wrap(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception as e:
            _logger.exception(str(e))
            return http.Response(response=str(e), status=500)
    return wrap


class SaasClient(http.Controller):
    """ 接收OAuth登录、刷新client信息的请求 """

    def _get_port(self):
        host_parts = request.httprequest.host.split(':')
        return len(host_parts) > 1 and host_parts[1] or 80

    def _get_port_str(self, scheme):
        port = str(self._get_port())
        if scheme == 'http' and port == '80' or scheme == 'https' and port == '443':
            return ''
        else:
            return ':' + port

    @http.route('/saas_client/oauth_login', type='http', auth='public', website=True)
    @fragment_to_query_string
    @webservice
    def oauth_login(self, **post):
        """ OAuth Login """
        _logger.info('oauth_login post: %s', post)

        scheme = request.httprequest.scheme
        port = self._get_port_str(scheme)
        state = simplejson.loads(post.get('state'))
        domain = state.get('host')

        if not state.get('p'):
            state['p'] = request.env.ref('saas_client.saas_oauth_provider').id

        params = {
            'access_token': post['access_token'],
            'state': simplejson.dumps(state),
        }
        url = '{scheme}://{domain}{port}/auth_oauth/signin?{params}'
        url = url.format(scheme=scheme, domain=domain, port=port, params=werkzeug.url_encode(params))
        return werkzeug.utils.redirect(url)

    @http.route(['/saas_client/sync_server'], type='http', auth='public')
    @webservice
    def sync_server(self, **post):
        """ Get client's users_num,file_storage and db_storage"""
        _logger.info('sync_server post: %s', post)

        state = simplejson.loads(post.get('state'))
        client_id = state.get('client_id')
        db = state.get('d')
        access_token = post['access_token']
        # get oauth_provider
        saas_oauth_provider = request.registry['ir.model.data'].xmlid_to_object(request.cr, SUPERUSER_ID,
                                                                                'saas_client.saas_oauth_provider')
        # tocken validation
        user_data = request.registry['res.users']._auth_oauth_rpc(request.cr, SUPERUSER_ID,
                                                                  saas_oauth_provider.validation_endpoint, access_token)
        if user_data.get("error"):
            raise Exception(user_data['error'])

        res = request.env['saas.sync.client'].sync_client(client_id, db)
        if res:
            return simplejson.dumps(res)
        else:
            raise Exception('Sync Client Failed!')

    @http.route(['/saas_client/db_backup'], type='http', auth='public')
    @webservice
    def db_backup(self, **post):
        """ backup database """
        _logger.info('db_backup post: %s', post)

        state = simplejson.loads(post.get('state'))
        client_id = state.get('client_id')
        db = state.get('d')
        save_days = state.get('save_days')
        access_token = post['access_token']
        # get oauth_provider
        saas_oauth_provider = request.registry['ir.model.data'].xmlid_to_object(request.cr, SUPERUSER_ID,
                                                                                'saas_client.saas_oauth_provider')
        # tocken validation
        user_data = request.registry['res.users']._auth_oauth_rpc(request.cr, SUPERUSER_ID,
                                                                  saas_oauth_provider.validation_endpoint, access_token)
        if user_data.get("error"):
            raise Exception(user_data['error'])

        res = request.env['saas.backup.db'].db_backup(client_id, db, save_days)
        if res:
            return simplejson.dumps(res)
        else:
            raise Exception('Backup Failed!')