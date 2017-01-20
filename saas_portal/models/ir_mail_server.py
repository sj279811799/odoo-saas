# -*- coding: utf-8 -*-

from openerp import models, api, tools


class EmabcMailServer(models.Model):
    _inherit = 'ir.mail_server'

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False):
        # Get SMTP Server Details from Mail Server
        mail_server = None
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
        elif not smtp_server:
            mail_server_ids = self.sudo().search([], order='sequence', limit=1)
            mail_server = mail_server_ids[0] if mail_server_ids else None

        if mail_server:
            smtp_user = mail_server.smtp_user
        else:
            # we were passed an explicit smtp_server or nothing at all
            smtp_user = smtp_user or tools.config.get('smtp_user')

        if message.has_key('Return-Path'):
            message.replace_header('Return-Path', '%s' % (smtp_user,))
        else:
            message.add_header('Return-Path', '%s' % (smtp_user,))

        super(EmabcMailServer, self).send_email(message, mail_server_id=mail_server_id, smtp_server=smtp_server,
                                                smtp_port=smtp_port,
                                                smtp_user=smtp_user, smtp_password=smtp_password,
                                                smtp_encryption=smtp_encryption,
                                                smtp_debug=smtp_debug)
