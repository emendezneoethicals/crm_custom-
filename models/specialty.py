from odoo import models, fields

class Specialty(models.Model):
    _name = 'res.specialty'
    _description = 'Especialidad'

    name = fields.Char(string="Nombre")
