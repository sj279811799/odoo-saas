# -*- coding: utf-8 -*-
""" Client端功能实现 """

import openerp
import logging
from openerp import api, models, fields, SUPERUSER_ID, exceptions
from datetime import datetime
from openerp.service.db import dump_db
import psycopg2
import os

_logger = logging.getLogger(__name__)

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


class SaasBackupDB(models.Model):
    _name = 'saas.backup.db'

    @api.model
    def backup(self, client_env, client_id, db_name, save_days):
        current_time = fields.Datetime.context_timestamp(client_env, datetime.now())
        try:
            backup_dir = '/var/lib/odoo/DBbackups/%s' % db_name
            if not os.path.isdir(backup_dir):
                os.makedirs(backup_dir)
        except:
            raise
        backup_file = '%s_%s.zip' % (db_name, current_time.strftime('%Y%m%d_%H_%M_%S'))
        file_path = os.path.join(backup_dir, backup_file)
        try:
            stream = dump_db(db_name, None)
            with open(file_path, 'w') as fp:
                for line in stream:
                    fp.write(line)
        except Exception as e:
            _logger.warning("Backup database %s except: %s" % (db_name, e))

        # 删除过期的备份
        if os.path.isdir(backup_dir):
            for f in os.listdir(backup_dir):
                full_path = os.path.join(backup_dir, f)
                delta = datetime.now() - datetime.fromtimestamp(os.stat(full_path).st_ctime)
                if delta.days >= save_days:
                    if os.path.isfile(full_path) and ".zip" in f:
                        _logger.info("Delete local out-of-date file: " + full_path)
                        os.remove(full_path)

    @api.model
    def db_backup(self, client_id, db_name, save_days):
        try:
            registry = self.registry(db_name)
            with registry.cursor() as client_cr:
                client_env = api.Environment(client_cr, SUPERUSER_ID, self._context)
                data = self.backup(client_env, client_id, db_name, save_days)
                return data
        except psycopg2.OperationalError:
            return False