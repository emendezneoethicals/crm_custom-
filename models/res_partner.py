from odoo import models, fields,api
import logging

_logger = logging.getLogger(__name__)
class ResPartner(models.Model):
    _inherit = 'res.partner'

    crm_lead_ids = fields.One2many('crm.lead', 'partner_id', string="Leads Relacionados")
    specialty_id = fields.Many2one('res.specialty', string="Especialidad",compute="_compute_specialty_leads", inverse="_inverse_specialty_leads", store=True)
    collegial_number = fields.Char(string="Colegiado")
    clinic_name = fields.Char(string="Nombre Clínica")
    clinic_address = fields.Text(string="Dirección")
    clinic_turn_id = fields.Many2one('turn',string="Gira",compute="_compute_clinic_turn_leads", inverse="_inverse_clinic_turn_leads", store=True)
    clinic_department = fields.Many2one('res.country.state', string='Departamento', related="clinic_municipality.state_id",store=True,readonly=True)
    clinic_municipality = fields.Many2one('municipality', string="Municipio",compute="_compute_clinic_municipality_leads",inverse="_inverse_clinic_municipality_leads",store=True, readonly=False)
    clinic_schedule = fields.Text(string="Horario de atención")
    secretary_name = fields.Char(string="Nombre Secretaria")
    clinic_phone = fields.Char(string= "Teléfono de la Clinica")
    secretary_phone = fields.Char(string= "Teléfono de la Secretaria")
    product_ids = fields.Many2many('product.template','partner_product_rel','partner_id','product_id',string='Productos')

    @api.depends('crm_lead_ids.specialty_id')
    def _compute_specialty_leads(self):
        """Obtiene specialty_id desde crm.lead si existe."""
        for partner in self:
            if partner.crm_lead_ids:
                partner.specialty_id = partner.crm_lead_ids[0].specialty_id

    def _inverse_specialty_leads(self):
        """Guarda specialty_id en crm.lead cuando cambia en res.partner."""
        for partner in self:
            for lead in partner.crm_lead_ids:
                lead.specialty_id = partner.specialty_id

    @api.depends('crm_lead_ids.clinic_turn_id')
    def _compute_clinic_turn_leads(self):
        """Obtiene clinic_turn_id desde crm.lead si existe."""
        for partner in self:
            if partner.crm_lead_ids:
                partner.clinic_turn_id = partner.crm_lead_ids[0].clinic_turn_id

    def _inverse_clinic_turn_leads(self):
        """Guarda clinic_turn_id en crm.lead cuando cambia en res.partner."""
        for partner in self:
            for lead in partner.crm_lead_ids:
                lead.clinic_turn_id = partner.clinic_turn_id


    @api.depends('crm_lead_ids.clinic_municipality')
    def _compute_clinic_municipality_leads(self):
        """Obtiene clinic_municipality desde crm.lead si existe."""
        for partner in self:
            if partner.crm_lead_ids:
                partner.clinic_municipality = partner.crm_lead_ids[0].clinic_municipality

    def _inverse_clinic_municipality_leads(self):
        """Guarda clinic_municipality en crm.lead cuando cambia en res.partner."""
        for partner in self:
            for lead in partner.crm_lead_ids:
                lead.clinic_municipality = partner.clinic_municipality

    def write(self, vals):
        """Sincroniza productos en CRM cuando se actualizan en Partner."""
        if self.env.context.get('skip_sync'):
            return super(ResPartner, self).write(vals)

        res = super(ResPartner, self).write(vals)
        if 'product_ids' in vals:
            for partner in self:
                for lead in partner.crm_lead_ids:
                    # Evitar actualizar si los valores ya son iguales
                    if set(lead.product_ids.ids) != set(partner.product_ids.ids):
                        # evitar actualización recursiva con with_context
                        lead.with_context(skip_sync=True).product_ids = partner.product_ids
        return res