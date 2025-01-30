from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one('res.partner', string="Contacto", ondelete='set null')
    specialty_id = fields.Many2one('res.specialty', string="Especialidad", compute="_compute_specialty", inverse="_inverse_specialty", store=True, readonly=False)
    collegial_number = fields.Char(string="Colegiado", related="partner_id.collegial_number", store=True, readonly=False)
    clinic_name = fields.Char(string="Nombre Clínica", related="partner_id.clinic_name", store=True, readonly=False)
    clinic_address = fields.Text(string="Dirección", related="partner_id.clinic_address", store=True, readonly=False)
    clinic_turn_id = fields.Many2one('turn', string="Gira",compute="_compute_clinic_turn", inverse="_inverse_clinic_turn", store=True, readonly=False)
    clinic_department = fields.Many2one('res.country.state', string='Departamento', related="clinic_municipality.state_id",store=True,readonly=True)
    clinic_municipality = fields.Many2one('municipality', string="Municipio", compute="_compute_clinic_municipality",inverse="_inverse_clinic_municipality",store=True, readonly=False)
    clinic_schedule = fields.Text(string="Horario de atención", related="partner_id.clinic_schedule", store=True, readonly=False)
    secretary_name = fields.Char(string="Nombre Secretaria", related="partner_id.secretary_name", store=True, readonly=False)
    clinic_priority = fields.Selection(
        [(str(i), f'{i} Estrella{"s" if i > 1 else ""}') for i in range(0, 6)],
        string="Clasificación",
        default='1',
    )

    @api.depends('partner_id.specialty_id')
    def _compute_specialty(self):
        """Obtiene la especialidad desde el partner automáticamente."""
        for lead in self:
            if lead.partner_id:
                lead.specialty_id = lead.partner_id.specialty_id

    def _inverse_specialty(self):
        """Guarda la especialidad en el partner cuando cambia en CRM."""
        for lead in self:
            if lead.partner_id and lead.specialty_id:
                lead.partner_id.specialty_id = lead.specialty_id

    @api.depends('partner_id.clinic_turn_id')
    def _compute_clinic_turn(self):
        """Obtiene la Gira desde el partner automáticamente."""
        for lead in self:
            if lead.partner_id:
                lead.clinic_turn_id = lead.partner_id.clinic_turn_id

    def _inverse_clinic_turn(self):
        """Guarda la Gira en el partner cuando cambia en CRM."""
        for lead in self:
            if lead.partner_id and lead.clinic_turn_id:
                lead.partner_id.clinic_turn_id = lead.clinic_turn_id
    
    @api.depends('partner_id.clinic_municipality')
    def _compute_clinic_municipality(self):
        """Obtiene la municipalidad desde el contacto automáticamente."""
        for lead in self:
            if lead.partner_id:
                lead.clinic_municipality = lead.partner_id.clinic_municipality

    def _inverse_clinic_municipality(self):
        """Guarda la municipalidad en el contacto cuando cambia en CRM."""
        for lead in self:
            if lead.partner_id and lead.clinic_municipality:
                lead.partner_id.clinic_municipality = lead.clinic_municipality