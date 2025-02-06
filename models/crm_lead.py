from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError

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
    clinic_phone = fields.Char(string= "Teléfono de la Clinica",related="partner_id.clinic_phone",store=True, readonly=False)
    secretary_phone = fields.Char(string= "Teléfono de la Secretaria ",related="partner_id.secretary_phone",store=True, readonly=False)
    purchased_product_ids = fields.Many2many('product.template', 'crm_lead_purchased_product_rel', 'lead_id', 'product_id',string="Productos Comprados", store=True,readonly=True)
    not_purchased_product_ids = fields.Many2many('product.template', 'crm_lead_not_purchased_product_rel', 'lead_id', 'product_id',string="Productos No Comprados", store=True,readonly=True)
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

    @api.depends('partner_id.product_ids')
    def _compute_products_from_partner(self):
        """Obtiene los productos desde el partner automáticamente."""
        for lead in self:
            if lead.partner_id:
                lead.product_ids = lead.partner_id.product_ids

   
    def write(self, vals):
        """
        Bloquea el cambio de estado si ciertos campos no están llenos.
        """
        # Detectar si se está intentando cambiar de estado (stage_id)
        if 'stage_id' in vals:
            for lead in self:
                
                required_fields = ['not_purchased_product_ids','clinic_name', 'clinic_turn_id', 'clinic_municipality','partner_id']

                # Verificar si algún campo obligatorio está vacío
                missing_fields = [field for field in required_fields if not lead[field]]
                
                if missing_fields:
                    raise ValidationError(
                        "No puedes cambiar de estado hasta completar los siguientes campos:\n" +
                        "\n".join(self._fields[field].string for field in missing_fields)
                    )

        return super(CrmLead, self).write(vals)

    @api.model
    def create(self, vals_list):
        """ 
        Al crear una nueva oportunidad, asigna los productos comprados y no comprados según la especialidad del médico.
        """
        lead = super(CrmLead, self).create(vals_list)

        if lead.partner_id:
            lead._set_initial_purchased_products()
        return lead
    


    def _set_initial_purchased_products(self):
        """ 
        Calcula los productos comprados/no comprados solo al crear una oportunidad nueva.
        """
        for lead in self:
            if not lead.partner_id:
                continue

            # Buscar productos de la especialidad del médico
            specialty_products = self.env['product.template'].search([
                ('specialty_ids', 'in', [lead.specialty_id.id])
            ])

            # Buscar los productos que ya ha comprado
            purchased_products = self.env['sale.order.line'].search([
                ('order_id.partner_id', '=', lead.partner_id.id),
                ('product_id.product_tmpl_id', 'in', specialty_products.ids),
                ('order_id.invoice_ids.state', '=', 'posted'),  
                ('order_id.invoice_ids.payment_state', '=', 'paid')  
            ])

            # Verificar devoluciones en stock.picking
            # Diccionario para acumular datos por producto (product.template)
            purchased_data = {} 

            for sale_line in purchased_products:
                pt_id = sale_line.product_id.product_tmpl_id.id
                sold_qty = sale_line.product_uom_qty
                if pt_id not in purchased_data:
                    purchased_data[pt_id] = {'sold': 0.0, 'returned': 0.0}
                purchased_data[pt_id]['sold'] += sold_qty

                _logger.warning("Procesando sale_line %s: Producto '%s' vendido en cantidad %s.",
                                sale_line.id, sale_line.product_id.name, sold_qty)

                # Buscar movimientos de stock asociados a esta línea de venta
                related_moves = self.env['stock.move'].search([
                    ('sale_line_id', '=', sale_line.id),
                    ('state', '=', 'done'),
                ])
                _logger.info("Sale_line %s: Se encontraron %s stock moves entregados.", sale_line.id, len(related_moves))

                # Buscar movimientos de devolución asociados a esos stock moves y para el mismo partner
                return_moves = self.env['stock.move'].search([
                    ('origin_returned_move_id', 'in', related_moves.ids),
                    ('state', '=', 'done'),
                    ('partner_id', '=', lead.partner_id.id),
                ])
                _logger.info("Sale_line %s: Se encontraron %s movimientos de devolución.", sale_line.id, len(return_moves))

                total_returned_qty = 0.0
                for move in return_moves:
                    converted_qty = move.product_uom._compute_quantity(move.quantity, sale_line.product_uom)
                    _logger.warning("Movimiento de devolución %s: Cantidad original %s, convertida a %s.",
                                    move.id, move.quantity, converted_qty)
                    total_returned_qty += converted_qty

                _logger.warning("Sale_line %s: Total cantidad devuelta = %s.", sale_line.id, total_returned_qty)

                purchased_data[pt_id]['returned'] += total_returned_qty

            # Ahora, para cada producto en la especialidad, calculamos el neto:
            purchased_product_ids = set()
            not_purchased_products = set()

            for product in specialty_products:
                pt_id = product.id
                sold = purchased_data.get(pt_id, {}).get('sold', 0.0)
                returned = purchased_data.get(pt_id, {}).get('returned', 0.0)
                net = sold - returned
                _logger.warning("Producto %s: vendido = %s, devuelto = %s, neto = %s.", product.name, sold, returned, net)
                if net > 0:
                    purchased_product_ids.add(pt_id)
                else:
                    not_purchased_products.add(pt_id)

            _logger.warning("Lead %s: Productos comprados (neto > 0): %s.", lead.id, purchased_product_ids)
            _logger.warning("Lead %s: Productos no comprados: %s.", lead.id, not_purchased_products)

            lead.write({
                'purchased_product_ids': [(6, 0, list(purchased_product_ids))],
                'not_purchased_product_ids': [(6, 0, list(not_purchased_products))],
            })
