# -*- coding: utf-8 -*
""" 用于接收来自Portal端的初始化请求 """
from openerp import http
from openerp.http import request
import simplejson
import functools
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


class ClientInit(http.Controller):
    """ 接收请求 """

    @http.route('/client_init/install_addons', type='http', auth='public')
    @webservice
    def install_addons(self, **post):
        """ 接收安装模块请求 """
        _logger.info('install_addons post: %s', post)

        state = simplejson.loads(post.get('state'))
        addons = state.get('addons', [])
        db_name = state.get('d')
        server_name = state.get('server_name')

        client = request.env['client.install.addons']
        client.install_addons(addons=addons, db_name=db_name, server_name=server_name)
        client.update_registry(db_name=db_name)

        return simplejson.dumps({
            'state': 'success',
        })
