# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_simulator module for OpenERP, Sale by assembly module
#    Copyright (C) 2014 Mirounga (<http://mirounga.fr>)
#                  Christophe CHAUVET <christophe.chauvet@gmail.com>
#
#    This file is a part of sale_simulator
#
#    sale_simulator is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_simulator is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Sale Simulator",
    "version": "1.1",
    "author": "Mirounga, Syleam",
    "website": "http://www.mirounga.fr/",
    "description": """
The sale simulator
    """,
    "category": "Generic Modules/Sale",
    "depends": [
        "base",
        "product",
        "sale",
        "mrp",
    ],
    "demo": [
        "demo/product.xml",
        "demo/sale_simulator.xml",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "sale_simulator_sequence.xml",
        "product_view.xml",
        "sale_view.xml",
        "partner_view.xml",
        "sale_simulator_wizard.xml",
    ],
    "test": [
        "test/compute_module_price.yml",
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
