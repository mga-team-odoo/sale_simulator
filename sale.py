# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Syleam Info Services (http://www.syleam.fr) All rights Reserved.
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
from openerp.tools.translate import _


class sale_simulator(orm.Model):
    '''
    Sale simulator
    '''
    _name = 'sale.simulator'
    _description = 'Sale simulator'
    _order = 'name'

    _columns = {
        'name': fields.char('Simulation number', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', ondelete='cascade', required=True),
        'line_ids': fields.one2many('sale.simulator.line', 'simul_id', 'Lines', required=True),
        'user_id': fields.many2one('res.users', 'Salesman', required=True, help="Salesman user"),
        'shop_id': fields.many2one('sale.shop', 'Shop', required=True, help='Select shop to convert this sale as sale order'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'sale.simulator'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'sale.simulator', context=c),
    }


class sale_simulator_line(orm.Model):
    '''
    Sale simulator line
    '''
    _name = 'sale.simulator.line'
    _description = 'Sale simulator line'
    _order = 'id'

    def _factory_price(self, cr, uid, ids, name, arg, context=None):
        '''
        Calcul le prix de revient de chaque composant.
        '''
        res = {}
        line_obj = self.pool.get('sale.simulator.line.item')
        for line in self.browse(cr, uid, ids, context=context):
            factory_price = line.item_id.factory_price

            # Récupération des modules
            mod_ids = line_obj.search(cr, uid, [('line_id', '=', line.id)], context=context)
            if mod_ids:
                for mod in line_obj.browse(cr, uid, mod_ids, context=context):
                    factory_price += round(mod.item_id2.factory_price, 2)
            res.setdefault(line.id, factory_price)
        return res

    def _retail_price(self, cr, uid, ids, name, arg, context=None):
        '''
        Calcul du prix de vente.
        '''
        res = {}
        line_obj = self.pool.get('sale.simulator.line.item')
        for line in self.browse(cr, uid, ids, context=context):
            # Récupération du produit de référence
            retail_price = line.item_id.retail_price

            # Récupération des modules
            mod_ids = line_obj.search(cr, uid, [('line_id', '=', line.id)])
            if mod_ids:
                for mod in line_obj.browse(cr, uid, mod_ids, context=context):
                    retail_price += round(mod.item_id2.retail_price, 2)
            res.setdefault(line.id, retail_price)
        return res

    def _margin(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            margin = round((line.sale_price - line.factory_price), 2)
            res.setdefault(line.id, margin)
        return res

    _columns = {
        'name': fields.char('Name', size=12, required=True),
        'description': fields.char('Description', size=64, required=True),
        'simul_id': fields.many2one('sale.simulator', 'Sale simulator', select=True, required=True, ondelete='cascade'),
        'item_id': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'quantity': fields.float('Quantity'),
        'factory_price': fields.function(_factory_price, method=True, type='float', string='Factory price'),
        'discount': fields.float('Discount'),
        'retail_price': fields.function(_retail_price, method=True, type='float', string='Retail price'),
        'margin': fields.function(_margin, method=True, type='float', string='Margin'),
        'sale_price': fields.float('Sale price'),
        'line_ids': fields.one2many('sale.simulator.line.item', 'line_id', 'Item', required=True),
        'order_id': fields.many2one('sale.order', 'Sale order'),
        'message': fields.char('Message', size=128),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'name': 'OK',
        'quantity': 1.0,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'sale.simulator', context=c),
        'quantity': 1.0,
    }

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def check_config(self, cr, uid, ids, context=None):
        '''
        Check if selected configuration is valid
        '''
        f_obj = self.pool.get('product.item.feature.line')
        sl_obj = self.pool.get('sale.simulator.line.item')
        config = self.read(cr, uid, ids, context=context)
        if not config:
            raise orm.except_orm(_('Error'), _('Configuration line not found'))

        for c in config:
            tf = {}
            nf = {}
            lf = {}

            # search feature in product item
            item_id = c['item_id'][0]
            f_id = f_obj.search(cr, uid, [('item_id', '=', item_id)], context=context)
            if not f_id:
                print '_check_config:f_id: not found !'

            feature_ids = f_obj.read(cr, uid, f_id, ['id', 'feature_id', 'quantity', 'global'], context=context)
            for f in feature_ids:
                tf[f['feature_id'][0]] = f['global']
                nf[f['feature_id'][0]] = f['feature_id'][1]
                lf[f['feature_id'][0]] = f['quantity']

            # check all modules
            for z_id in c['line_ids']:
                module_id = sl_obj.read(cr, uid, z_id, ['id', 'item_id2'], context=context)
                if not module_id:
                    raise orm.except_orm(_('Error'), _('No module found for %d !') % z_id)

                fmod_args = [('item_id', '=', module_id['item_id2'][0])]
                fmod_ids = f_obj.search(cr, uid, fmod_args, context=context)
                if fmod_ids:
                    fitem_ids = f_obj.read(cr, uid, fmod_ids, ['id', 'feature_id', 'quantity', 'global'], context=context)
                    if fitem_ids:
                        for mf in fitem_ids:
                            lf[mf['feature_id'][0]] += mf['quantity']

            msg = True
            # Check if max config is superior
            for k in tf.keys():
                if k in lf and tf[k] < lf[k]:
                    msg = False
                    rew = self.write(cr, uid, ids, {
                        'message': 'Feature (%s) overload vals:%s max:%s' % (nf[k], str(lf[k]), str(tf[k]))
                    }, context=context)

            if msg:
                rew = self.write(cr, uid, ids, {'message': 'Configuration valid'}, context=context)
                if not rew:
                    raise orm.except_orm(_('Error'), _('Cannot print error message on the line'))

        return True

    def onchange_discount(self, cr, uid, ids, item_id, discount, retail_price):
        v = {}
        if item_id:
            v['sale_price'] = retail_price - (retail_price * discount / 100)

        return {'value': v}

    def onchange_saleprice(self, cr, uid, ids, item_id, retail_price, sale_price):
        v = {}
        if item_id:
            if retail_price <= 0:
                v['discount'] = 0
            else:
                v['discount'] = 100 - (sale_price * 100 / retail_price)

        return {'value': v}

    def onchange_product(self, cr, uid, ids, item_id, name):
        v = {}
        if item_id:
            product_item = self.pool.get('product.item').browse(cr, uid, item_id)
            v['sale_price'] = product_item.retail_price
            if not name:
                v['description'] = product_item.name

        return {'value': v}

    def create_sale_order(self, cr, uid, ids, context=None):
        """
        Create the sale order and the product with the BOM structure
        """
        if len(ids) > 1:
            raise orm.except_orm(_('Error'), _('You can only create one sale order at the time!'))

        simul_obj = self.pool.get('sale.simulator')
        simul = simul_obj.browse(cr, uid, ids[0], context=context)
        if not simul:
            raise orm.except_orm(_('Error'), _('Line not found, please reload your browser!'))


        return True

class sale_simulator_line_item(orm.Model):
    _name = 'sale.simulator.line.item'
    _description = 'Sale simulator line item'
    _order = 'id'

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for read in self.read(cr, uid, ids, ['line_id', 'item_id2'], context=context):
            res.append(read['id'], 'OK')
        return res

    _columns = {
        'name': fields.char('Name', size=12, required=True),
        'line_id': fields.many2one('sale.simulator.line', 'Sale simulator line', required=True, select=True),
        'item_id2': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'retail_price': fields.float('Retail price'),
        'factory_price': fields.float('Factory Price'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'name': 'OK',
        'retail_price': 0.0,
        'factory_price': 0.0,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'sale.simulator', context=c),
    }

    def onchange_item(self, cr, uid, ids, item_id, context=None):
        '''
        If item change, retrieve the factory and retail price
        '''
        if not item_id:
            return {}

        if context is None:
            context = self.pool.get('res.users').context_get(cr, uid)

        v = {}
        item = self.pool.get('product.item').browse(cr, uid, item_id, context=context)
        if item:
            v.update({
                'factory_price': item.factory_price,
                'retail_price': item.retail_price,
            })

        return {'value': v}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
