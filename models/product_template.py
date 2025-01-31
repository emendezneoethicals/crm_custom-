from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    specialty_ids = fields.Many2many(
        'res.specialty', 'product_specialty_rel', 'product_id', 'specialty_id',
        string="Especialidades Médicas"
    )
