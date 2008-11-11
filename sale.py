# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Sylëam Info Services (http://www.syleam.fr) All rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields, osv

class sale_simulator(osv.osv):
    '''
    Sale simulator
    '''
    _name = 'sale.simulator'
    _description = 'Sale simulator'

    _columns = {
        'name': fields.char('Simulation number', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'pricelist_id': fields.many2one('product.pricelist','Price List', ondelete='cascade'),
        'line_ids': fields.one2many('sale.simulator.line','simul_id', 'Lines'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'sale.simulator'),
    }

sale_simulator()

class sale_simulator_line(osv.osv):
    '''
    Sale simulator line
    '''
    _name = 'sale.simulator.line'
    _description = 'Sale simulator line'

    def _factory_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for id in ids:
            res.setdefault(id, 10.0)
        return res

    def _retail_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for id in ids:
            res.setdefault(id, 1998.50)
        return res

    def _margin(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for id in ids:
            res.setdefault(id, 18.0)
        return res

    _columns = {
        'description': fields.char('Description', size=64, required=True),
        'simul_id': fields.many2one('sale.simulator', 'Sale simulator', required=True, ondelete='cascade'),
        'item_id': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'quantity': fields.float('Quantity'),
        'factory_price': fields.function(_factory_price, method=True, type='float', string='Factory price'),
        'discount': fields.float('Discount'),
        'retail_price': fields.function(_retail_price, method=True, type='float', string='Retail price'),
        'margin': fields.function(_margin, method=True, type='float', string='Margin'),
        'sale_price': fields.float('Sale price'),
        'line_ids': fields.one2many('sale.simulator.line.item','line_id','Item'),
    }

    _defaults = {
        'quantity': lambda *a: 1.0,
    }

sale_simulator_line()

class sale_simulator_line_item(osv.osv):
    _name = 'sale.simulator.line.item'
    _description = 'Sale simulator line item'

    _columns = {
        'line_id': fields.many2one('sale.simulator.line', 'Sale simulator line', required=True, ondelete='cascade'),
        'item_id2': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'retail_price': fields.float('Retail price'),
        'factory_price': fields.float('Factory Price'),
    }

    _defaults = {
        'retail_price': lambda *a: 0.0,
        'factory_price': lambda *a: 0.0,
    }

sale_simulator_line_item()
