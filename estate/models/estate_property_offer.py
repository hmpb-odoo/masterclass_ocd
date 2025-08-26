from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate property offer model"

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

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for property in self:
            property.date_deadline = (property.create_date or fields.Date.today()) +  relativedelta(days=property.validity)

    def _inverse_date_deadline(self):
        for property in self:
            property.validity = (property.date_deadline - property.create_date.date()).days if property.create_date and property.date_deadline else False
