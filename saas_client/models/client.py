# -*- coding: utf-8 -*-
""" Client端功能实现 """
import openerp
from openerp import api, models, fields, SUPERUSER_ID, exceptions
import psycopg2
import os


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


class SaasSyncClient(models.Model):
    """ Sync Client """
    _name = 'saas.sync.client'

    @api.model
    def registry(self, db_name, new=False, **kwargs):
        """ 获取DB实例 """
        m = openerp.modules.registry.RegistryManager
        if new:
            return m.new(db_name, **kwargs)
        else:
            return m.get(db_name, **kwargs)

    @api.model
    def _get_data(self, client_env, check_client_id, db_name):
        """ 获取CLient users_num,file_storage and db_storage """

        # 客户端验证
        # client_id = client_env['ir.config_parameter'].get_param('database.uuid')
        # if check_client_id != client_id:
        #     return False

        # 用户数量（admin用户除外）
        users = client_env['res.users'].search([('share', '=', False), ('id', '!=', SUPERUSER_ID)])
        users_len = len(users)

        # 附件存储
        data_dir = openerp.tools.config['data_dir']
        file_storage = get_size('%s/filestore/%s' % (data_dir, db_name))
        file_storage = int(file_storage / (1024 * 1024))

        # 数据库存储
        client_env.cr.execute("select pg_database_size('%s')" % db_name)
        db_storage = client_env.cr.fetchone()[0]
        db_storage = int(db_storage / (1024 * 1024))

        data = {
            'users_len': users_len,
            'file_storage': file_storage,
            'db_storage': db_storage,
        }
        return data

    @api.model
    def sync_client(self, client_id, db_name):
        try:
            registry = self.registry(db_name)
            with registry.cursor() as client_cr:
                client_env = api.Environment(client_cr, SUPERUSER_ID, self._context)
                data = self._get_data(client_env, client_id, db_name)
                return data
        except psycopg2.OperationalError:
            return False



