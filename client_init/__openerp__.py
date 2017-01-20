# -*- coding: utf-8 -*-
{
    'name': "Client Init",

    'summary': """
        Client Init
    """,

    'description': """
        Client Init
    """,

    'author': "Hand",
    'website': "http://www.hand-china.com",
    'category': '',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
    ],

    'qweb': [
        'static/src/xml/*.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
