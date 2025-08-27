from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Estate property type model"

    name = fields.Char(required=True)

    _sql_constraints = [
        ("unique_name", "unique(name)", "The name should be unique")
    ]
