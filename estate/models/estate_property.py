from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate property model"
    _order = "id desc"


    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=lambda self: fields.Date.context_today(self) + relativedelta(months=3))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        selection=[
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ],
    )
    estate = fields.Selection(
        selection=[
            ("new", "New"),
            ("offer_received", "Offer Received"),
            ("offer_accepted", "Offer Accepted"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        copy=False,
        default="new"
    )

    property_type_id = fields.Many2one('estate.property.type')
    buyer_id = fields.Many2one('res.partner')
    salesperson_id = fields.Many2one('res.users')

    tag_ids = fields.Many2many('estate.property.tag')
    offer_ids = fields.One2many('estate.property.offer', 'property_id')

    total_area = fields.Float(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")

    _sql_constraints = [
        (
            "check_expected_price_strictly_positive",
            "CHECK(expected_price > 0)",
            "The expected price must be strictly positive."
        ),
        (
            "check_selling_price_positive",
            "CHECK(selling_price >= 0)",
            "The selling price must be zero or positive."
        )
    ]

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for property in self:
            property.total_area = property.living_area + property.garden_area 

    @api.depends("offer_ids.price")    
    def _compute_best_price(self):
        for property in self:
            property.best_price = max(property.offer_ids.mapped('price')) if property.offer_ids else False

    @api.onchange("garden")
    def _onchange_garden(self):
        self.garden_area = 10 if self.garden else False
        self.garden_orientation = 'north' if self.garden else False

    def action_sold(self):
        self.ensure_one()
        if self.estate in ('sold', 'cancelled'):
            raise UserError(_('This property cannot be sold'))
        else:
            self.estate = 'sold'

    def action_cancel(self):
        self.ensure_one()
        if self.estate in ('sold', 'cancelled'):
            raise UserError(_('This property cannot be cancel'))
        else:
            self.estate = 'cancelled'

    @api.constrains('selling_price', 'expected_price', 'estate')
    def check_prices(self):
        for property in self:
            min_price = property.expected_price * 0.9
            if float_is_zero(property.selling_price, precision_rounding=0.01):
                continue
            elif float_compare(property.selling_price, min_price, precision_rounding=0.01) < 0:
                raise ValidationError(
                    "The selling price cannot be lower than 90% of the expected price."
                )

    def unlink(self):
        if not set(self.mapped("estate")) <= {"new", "cancelled"}:
            raise UserError("Only new and canceled properties can be deleted.")
        return super().unlink()
