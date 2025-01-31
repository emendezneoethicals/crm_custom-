from odoo import models, fields

class Turn(models.Model):
    _name = 'turn'
    _description = 'Gira'

    name = fields.Char(string="Nombre de la gira")
    description = fields.Text(string ="Descripcion")
    start_date = fields.Date(string = "Fecha de Inicio")
    end_date = fields.Date(string = "Fecha Final") 
    company_id = fields.Many2one('res.company',string='Compañía',default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country',string='País de la Compañía',related='company_id.country_id',store=True,readonly=True)
    location_id = fields.Many2one('res.country.state', string='Destino', domain="[('country_id', '=', country_id)]")
    adrres = fields.Text(string ="Dirección exacta")