from odoo import models, fields

class ResCountryMunicipality(models.Model):
    _name = 'municipality'
    _description = 'Municipios de un Departamento'

    name = fields.Char(string="Nombre del Municipio", required=True)
    state_id = fields.Many2one('res.country.state', string="Departamento", domain="[('country_id', '=', country_id)]", required=True)
    company_id = fields.Many2one('res.company',string='Compañía',default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country',string='País de la Compañía',related='company_id.country_id',store=True,readonly=True)
