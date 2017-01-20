# -*- coding: utf-8 -*-
{
    'name': "SaaS",

    'summary': """
        SaaS
    """,

    'description': """
        SaaS
    """,

    'author': "Hand",
    'website': "http://www.hand-china.com",
    'category': '',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['mail', 'oauth_provider', 'auth_oauth'],

    # always loaded
    'data': [
        'views/saas_view.xml',
        'views/saas_nginx.xml',
        'views/templates.xml',
        'views/webclient_templates.xml',
        'views/res_config.xml',
        'data/saas_data.xml',
    ],

    'qweb': [
        'static/src/xml/*.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
