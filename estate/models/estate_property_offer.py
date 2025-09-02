from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare




class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate property offer model"
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection(
        selection=[
            ("accepted", "Accepted"),
            ("refused", "Refused"),
        ],
    )
    partner_id = fields.Many2one('res.partner')
    property_id = fields.Many2one('estate.property')

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline")

    _sql_constraints = [
        (
            "check__price_strictly_positive",
            "CHECK(price > 0)",
            "The price must be strictly positive."
        ),
    ]

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for offer in self:
            offer.date_deadline = (offer.create_date or fields.Date.today()) +  relativedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            offer.validity = (offer.date_deadline - offer.create_date.date()).days if offer.create_date and offer.date_deadline else False

    def action_accept(self):
        self.ensure_one()
        if self.status  and self.status in ('accepted'):
            raise UserError(_('This offer is already accepted'))
        elif self.property_id.estate in ('sold', 'cancelled'):
            raise UserError(_('This property cannot accept new offers'))
        else:
            self.status = 'accepted'
            self.property_id.estate = 'offer_accepted'
            self.property_id.buyer_id = self.partner_id
            self.property_id.selling_price = self.price
    
    def action_refuse(self):
        self.ensure_one()
        if self.status and self.status in ('refused'):
            raise UserError(_('This offer is already refused'))
        else:
            self.status = 'refused'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("property_id") and vals.get("price"):
                prop = self.env["estate.property"].browse(vals["property_id"])
                # We check if the offer is higher than the existing offers
                if prop.offer_ids:
                    max_offer = max(prop.mapped("offer_ids.price"))
                    if float_compare(vals["price"], max_offer, precision_rounding=0.01) <= 0:
                        raise UserError("The offer must be higher than %.2f" % max_offer)
                prop.estate = "offer_received"
            return super().create(vals)
