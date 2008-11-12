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

#
# Feature list
#
class product_item_feature(osv.osv):
    '''
    Item feature list
    '''
    _name = 'product.item.feature'
    _description = 'Product feature list'

    _columns = {
        'code': fields.char('Code', size=10, required=True),
        'name': fields.char('Name', size=64, required=True, translate=True),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': lambda *a: True,
    }

    _order = 'code'

product_item_feature()

#
# PRODUCT ITEM
#
class product_item(osv.osv):
    '''
    Item list of product
    '''
    _name = 'product.item'
    _description = 'Product item'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=12, required=True),
        'type': fields.selection([('p','Product'),('m','Module')],'Type', required=True),
        'active': fields.boolean('Active'),
        'item_ids': fields.one2many('product.item.line', 'item_id', 'Item line'),
        'p_item_id': fields.many2one('product.item', 'Product Item', ondelete='cascade'),
        'feature_ids': fields.one2many('product.item.feature.line', 'item_id', 'Feature'),
        'number': fields.char('Product number', size=64),
        'factory_price': fields.float('Factory price'),
        'retail_price': fields.float('Retail price'),
        'capacity_start': fields.float('Capacity (To)'),
    }

    _defaults = {
        'active': lambda *a: True,
    }

product_item()

#
# PRODUCT ITEM LINE
#
class product_item_line(osv.osv):
    '''
    Product item line.
    '''
    _name = 'product.item.line'
    _description = 'Product Item Line'

    _columns = {
        'item_id': fields.many2one('product.item', 'Item', required=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'quantity': fields.float('Quantity', required=True),
        'uom_id': fields.many2one('product.uom', 'Unit', required=True),
    }

product_item_line()


class product_item_feature_line(osv.osv):
    '''
    Product item feature line
    '''
    _name = 'product.item.feature.line'
    _description = 'Product item feature line'

    _columns = {
        'item_id': fields.many2one('product.item', 'Item', required=True, ondelete='cascade'),
        'feature_id': fields.many2one('product.item.feature', 'Feature', required=True),
        'quantity': fields.float('Quantity',required=True),
        'global': fields.float('Global', required=True),
    }

product_item_feature_line()


