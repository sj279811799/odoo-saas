# -*- coding: utf-8 -*-
{
    'name': "SaaS Client",

    'summary': """
        SaaS Client""",

    'description': """
        SaaS Client
    """,

    'author': "Hand",
    'website': "http://www.hand-china.com",
    'category': '',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['auth_oauth'],

    # always loaded
    'data': [
        'data/client_data.xml',
        'data/pre_install.yml',
    ],

    'qweb': [
        'static/src/xml/*.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
