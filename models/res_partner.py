from odoo import models, fields,api
import logging
from odoo.exceptions import ValidationError

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
    purchased_product_ids = fields.Many2many('product.template','res_partner_purchased_product_rel','partner_id','product_id',string="Productos Comprados",store=True,readonly=True)
    not_purchased_product_ids = fields.Many2many('product.template','res_partner_not_purchased_product_rel','partner_id','product_id',string="Productos No Comprados",store=True,readonly=True)

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
    
    def action_update_purchased_products(self):
        """
        Recalcula los productos comprados y no comprados para este partner
        basado en las líneas de venta y sus devoluciones, según la especialidad.
        """
        for partner in self:
            if not partner.specialty_id:
                raise ValidationError("No se puede actualizar, el campo Especialidad esta vacio")
                continue

            # Buscar productos de la especialidad asignada al partner
            specialty_products = self.env['product.template'].search([
                ('specialty_ids', 'in', [partner.specialty_id.id])
            ])

            # Buscar todas las líneas de venta para este partner
            purchased_products = self.env['sale.order.line'].search([
                ('order_id.partner_id', '=', partner.id),
                ('product_id.product_tmpl_id', 'in', specialty_products.ids),
                ('order_id.invoice_ids.state', '=', 'posted'),
                ('order_id.invoice_ids.payment_state', '=', 'paid'),
            ])

            # Diccionario para acumular datos por producto (product.template)
            purchased_data = {}
            for sale_line in purchased_products:
                pt_id = sale_line.product_id.product_tmpl_id.id
                sold_qty = sale_line.product_uom_qty
                if pt_id not in purchased_data:
                    purchased_data[pt_id] = {'sold': 0.0, 'returned': 0.0}
                purchased_data[pt_id]['sold'] += sold_qty

                _logger.debug("Procesando sale_line %s: Producto '%s' vendido en cantidad %s.",
                              sale_line.id, sale_line.product_id.name, sold_qty)

                # Obtener los movimientos de stock asociados a la línea de venta
                related_moves = sale_line.move_ids.filtered(lambda m: m.state == 'done')
                _logger.debug("Sale_line %s: Se encontraron %s stock moves entregados.",
                              sale_line.id, len(related_moves))

                # Buscar movimientos de devolución asociados a esos movimientos y filtrando por partner
                return_moves = self.env['stock.move'].search([
                    ('origin_returned_move_id', 'in', related_moves.ids),
                    ('state', '=', 'done'),
                    ('partner_id', '=', partner.id),
                ])
                _logger.debug("Sale_line %s: Se encontraron %s movimientos de devolución.",
                              sale_line.id, len(return_moves))

                total_returned_qty = 0.0
                for move in return_moves:
                    converted_qty = move.product_uom._compute_quantity(move.quantity, sale_line.product_uom)
                    _logger.debug("Movimiento de devolución %s: Cantidad original %s, convertida a %s.",
                                  move.id, move.quantity, converted_qty)
                    total_returned_qty += converted_qty

                _logger.debug("Sale_line %s: Total cantidad devuelta = %s.", sale_line.id, total_returned_qty)
                purchased_data[pt_id]['returned'] += total_returned_qty

            # Calcular la cantidad neta por producto y determinar en qué lista debe estar
            purchased_product_ids = set()
            not_purchased_products = set()
            for product in specialty_products:
                pt_id = product.id
                sold = purchased_data.get(pt_id, {}).get('sold', 0.0)
                returned = purchased_data.get(pt_id, {}).get('returned', 0.0)
                net = sold - returned
                _logger.debug("Producto %s: vendido = %s, devuelto = %s, neto = %s.", product.name, sold, returned, net)
                if net > 0:
                    purchased_product_ids.add(pt_id)
                else:
                    not_purchased_products.add(pt_id)

            _logger.debug("Partner %s: Productos comprados (neto > 0): %s.", partner.id, purchased_product_ids)
            _logger.debug("Partner %s: Productos no comprados: %s.", partner.id, not_purchased_products)

            partner.write({
                'purchased_product_ids': [(6, 0, list(purchased_product_ids))],
                'not_purchased_product_ids': [(6, 0, list(not_purchased_products))],
            })
        return True
        