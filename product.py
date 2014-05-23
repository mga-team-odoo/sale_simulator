# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Sylëam Info Services (http://www.syleam.fr) All rights Reserved.
#               2013 Christophe CHAUVET <christophe.chauvet@gmail.com>
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

from openerp.osv import orm
from openerp.osv import fields
import openerp.addons.decimal_precision as dp


class product_item_feature(orm.Model):
    '''
    Item feature list
    '''
    _name = 'product.item.feature'
    _description = 'Product feature list'
    _order = 'code'

    _columns = {
        'code': fields.char('Code', size=10, required=True),
        'name': fields.char('Name', size=64, required=True, translate=True),
        'active': fields.boolean('Active'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'active': True,
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'product.item.feature', context=c),
    }

    def create(self, cr, uid, values, context=None):
        """
        #TODO make doc string
        Comment this
        """
        if context is None:
            context = {}

        if not values.get('code', False):
            values['code'] = 'NONE'

        return super(product_item_feature, self).create(cr, uid, values, context=context)

BOM_STEP = [
    (-1, 'Kit'),
    (1, 'Normal'),
    (2, 'BOM'),
]

ITEM_TYPE = [
    ('p', 'Product'),
    ('m', 'Module')
]


class product_item(orm.Model):
    '''
    List Items of product
    '''
    _name = 'product.item'
    _description = 'Product item'

    def _total_standard_price(self, cr, uid, ids, name, arg, context=None):
        '''
        Compute all products standard price.
        TODO: Maybe use a pricelist, to compute purchase price
        '''
        line_obj = self.pool['product.item.line']
        res = {}
        for id in ids:
            std_price = 0.0
            line_ids = line_obj.search(cr, uid, [('item_id', '=', id)], context=context)
            for line in line_obj.browse(cr, uid, line_ids, context=context):
                std_price += line.product_id.standard_price
            res.setdefault(id, std_price)
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=12, required=True),
        'type': fields.selection(ITEM_TYPE, 'Type', required=True),
        'active': fields.boolean('Active'),
        'item_ids': fields.one2many('product.item.line', 'item_id', 'Item line'),
        'p_item_id': fields.many2one('product.item', 'Product Item', ondelete='cascade'),
        'feature_ids': fields.one2many('product.item.feature.line', 'item_id', 'Feature'),
        'number': fields.char('Product number', size=64),
        'factory_price': fields.float('Factory price', help="Price include purchase price and others costs"),
        'retail_price': fields.float('Retail price'),
        'capacity_start': fields.float('Capacity'),
        'sequence': fields.integer('Sequence'),
        'bom_type': fields.selection(BOM_STEP, 'BOM type', required=True),
        'sale_taxes_id': fields.many2many('account.tax', 'sale_simulator_taxes_rel', 'item_id', 'tax_id', 'Customer taxes'),
        'categ_id': fields.many2one('product.category', 'Category'),
        'uom_id': fields.many2one('product.uom', 'Unit'),
        'notes': fields.text('Notes'),
        #        'tsp': fields.function(_total_standard_price, method=True, type='float', string='Total standard price'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'supplier_id': fields.many2one('res.partner', 'Supplier', help="Select the manufacturer if you use subcontracting,\nleave empty if you don't ue it"),
        'product_company_id': fields.many2one('res.company', 'Company', help='Company to create the main product,\nleave empty to create in the current company'),
        'routing_id': fields.many2one('mrp.routing', 'Routing', help='Select routing for this BOM'),
        'supply_method': fields.selection([('produce','Manufacture'),('buy','Buy')], 'Supply Method',
                                          help="Manufacture: When procuring the product, a manufacturing order or a task will be generated, depending on the product type. \nBuy: When procuring the product, a purchase order will be generated."),
    }

    _defaults = {
        'active': True,
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'product.item', context=c),
        'type': 'p',
        'sequence': 10,
        'bom_type': -1,
        'supplier_id': False,
        'routing_id': False,
        'supply_method': 'produce',
    }

    def price_compute(self, cr, uid, ids, context=None):
        """
        Compute the public price and the standard price of this module
        """
        if context is None:
            context = {}

        for itm in self.browse(cr, uid, ids, context=context):
            std_price = 0.0
            pub_price = 0.0
            for line in itm.item_ids:
                std_price += line.product_id.standard_price * line.quantity
                pub_price += line.product_id.list_price * line.quantity

            self.write(cr, uid, [itm.id], {'factory_price': std_price, 'retail_price': pub_price}, context=context)
        return True


class product_item_line(orm.Model):
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
        'list_price': fields.float('Sale Price', digits_compute=dp.get_precision('Product Price'),
                                   help="Base price to compute the customer price. Sometimes called the catalog price."),
        'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Product Price'),
                                       help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user"),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'product.item', context=c),
        'quantity': 1.0,
        'standard_price': 0.0,
        'list_price': 0.0,
    }

    def onchange_product(self, cr, uid, ids, product_id, context=None):
        '''
        If product change
        '''
        v = {}
        if product_id:
            product = self.pool['product.product'].browse(cr, uid, product_id, context=context)
            if product:
                v.update({
                    'uom_id': product.uom_id.id,
                    'standard_price': product.standard_price or 0.0,
                    'list_price': product.list_price or 0.0,
                })
            v['quantity'] = 1

        return {'value': v}


class product_item_feature_line(orm.Model):
    '''
    Product item feature line
    '''
    _name = 'product.item.feature.line'
    _description = 'Product item feature line'

    _columns = {
        'item_id': fields.many2one('product.item', 'Item', required=True, ondelete='cascade'),
        'feature_id': fields.many2one('product.item.feature', 'Feature', required=True),
        'quantity': fields.float('Quantity', required=True),
        'global': fields.float('Global', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'product.item', context=c),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
