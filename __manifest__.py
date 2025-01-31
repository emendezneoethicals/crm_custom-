{
    'name': 'CRM custom',
    'version': '1.0',
    'summary': '',
    'description': '',
    'category': 'CRM',
    'author': 'Angel Mendez - Neoethicals',
    'license': 'LGPL-3',
    'depends': ['crm','base', 'contacts','stock','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/municipality_views.xml',
        'views/crm_lead_views.xml',
        'views/specialty_views.xml',
        'views/turn_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        
        
    ],
    'installable': True,
    'application': False,
}
