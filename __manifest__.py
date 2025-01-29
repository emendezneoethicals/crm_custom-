{
    'name': 'CRM custom',
    'version': '1.0',
    'summary': '',
    'description': '',
    'category': 'CRM',
    'author': 'Angel Mendez - Neoethicals',
    'depends': ['crm','base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/specialty_views.xml',
        'views/turn_views.xml',
        'views/res_partner_views.xml',
        
        
    ],
    'installable': True,
    'application': False,
}
