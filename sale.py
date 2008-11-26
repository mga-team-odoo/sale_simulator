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
        'pricelist_id': fields.many2one('product.pricelist','Price List', ondelete='cascade', required=True),
        'line_ids': fields.one2many('sale.simulator.line','simul_id', 'Lines', required=True),
        'user_id': fields.many2one('res.users', 'Salesman', required=True, select=True),
        'shop_id': fields.many2one('sale.shop', 'Shop', required=True),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'sale.simulator'),
    }

    _order = 'name'

sale_simulator()

class sale_simulator_line(osv.osv):
    '''
    Sale simulator line
    '''
    _name = 'sale.simulator.line'
    _description = 'Sale simulator line'

    def _factory_price(self, cr, uid, ids, name, arg, context={}):
        '''
        Calcul le prix de revient de chaque composant.
        '''
        res = {}
        line_obj = self.pool.get('sale.simulator.line.item')
        for id in ids:
            line = self.browse(cr, uid, id)
            factory_price = line.item_id.factory_price
            # Récupération des modules
            mod_ids = line_obj.search(cr, uid, [('line_id','=',id)])
            for mod_id in mod_ids:
                mod = line_obj.browse(cr, uid, mod_id)
                factory_price += round(mod.item_id2.factory_price, 2)
            res.setdefault(id, factory_price)
        return res

    def _retail_price(self, cr, uid, ids, name, arg, context={}):
        '''
        Calcul du prix de vente.
        '''
        res = {}
        line_obj = self.pool.get('sale.simulator.line.item')
        for id in ids:
            line = self.browse(cr, uid, id)
            # Récupération du produit de référence
            retail_price = line.item_id.retail_price
            # Récupération des modules
            mod_ids = line_obj.search(cr, uid, [('line_id','=',id)])
            for mod_id in mod_ids:
                mod = line_obj.browse(cr, uid, mod_id)
                retail_price += round(mod.item_id2.retail_price, 2)
            res.setdefault(id, retail_price)
        return res

    def _margin(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for id in ids:
            line = self.browse(cr, uid, id)
            margin = round((line.sale_price - line.factory_price),2)
            res.setdefault(id, margin)
        return res

    _columns = {
        'name': fields.char('Name', size=12, required=True),
        'description': fields.char('Description', size=64, required=True),
        'simul_id': fields.many2one('sale.simulator', 'Sale simulator', required=True, ondelete='cascade'),
        'item_id': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'quantity': fields.float('Quantity'),
        'factory_price': fields.function(_factory_price, method=True, type='float', string='Factory price'),
        'discount': fields.float('Discount'),
        'retail_price': fields.function(_retail_price, method=True, type='float', string='Retail price'),
        'margin': fields.function(_margin, method=True, type='float', string='Margin'),
        'sale_price': fields.float('Sale price'),
        'line_ids': fields.one2many('sale.simulator.line.item','line_id','Item',required=True),
        'order_id': fields.many2one('sale.order', 'Sale order'),
    }

    _defaults = {
        'name': lambda *a: 'OK',
        'quantity': lambda *a: 1.0,
    }

    _order = 'id'

    def button_dummy(self, cr, uid, ids, context={}):
        return True

    def _check_config(self, cr, uid, ids, context={}):
        '''
        Check if selected configuration is valid
        '''
        config = self.read(cr, uid, ids)
        if not config:
            print '_check_config:config: not found !'
            return False
        for c in config:
            tf = {}
            nf = {}
            lf = {}

            # search feature in product item
            item_id = c['item_id'][0]
            f_obj = self.pool.get('product.item.feature.line')
            f_id = f_obj.search(cr, uid, [('item_id','=',item_id)])
            if not f_id:
                print '_check_config:f_id: not found !'

            feature_ids = self.pool.get('product.item.feature.line').read(cr, uid, f_id, ['id','feature_id', 'quantity', 'global'], context)
            for f in feature_ids:
                tf[f['feature_id'][0]] = f['global']
                nf[f['feature_id'][0]] = f['feature_id'][1]
                lf[f['feature_id'][0]] = f['quantity']

            # check all modules
            for z_id in c['line_ids']:
                module_id = self.pool.get('sale.simulator.line.item').read(cr, uid, z_id, ['id','item_id2'])
                if not module_id:
                    print '_check_config:module_ids: erreur '

                fline_obj = self.pool.get('product.item.feature.line')
                fmod_args = [('item_id','=', module_id['item_id2'][0])]
                fmod_ids = fline_obj.search(cr, uid, fmod_args)
                if fmod_ids:
                    fitem_ids = fline_obj.read(cr, uid, fmod_ids, ['id','feature_id', 'quantity', 'global'],context)
                    if fitem_ids:
                        #print '_check_config:fitem_ids: %s' % str(fitem_ids)
                        for mf in fitem_ids:
                            lf[mf['feature_id'][0]] += mf['quantity']

            # Check if max config is superior
            for k in tf.keys():
                if k in lf and tf[k] < lf[k]:
                    raise  osv.except_osv('Error !','Caractéristique (%s) dépassée qté:%s max:%s !' % (nf[k],str(lf[k]),str(tf[k])))

        return True

    #
    # On change method
    #
    def onchange_discount(self, cr, uid, ids, item_id, discount, retail_price):
        v= {}
        if item_id:
            v['sale_price'] = retail_price - (retail_price * discount / 100)
            #v['sale_price'] = 1001

        return {'value': v}

    def onchange_saleprice(self, cr, uid, ids, item_id, retail_price, sale_price):
        v = {}
        if item_id:
            v['discount'] = 100 - (sale_price * 100 / retail_price)

        return {'value': v}



sale_simulator_line()

class sale_simulator_line_item(osv.osv):
    _name = 'sale.simulator.line.item'
    _description = 'Sale simulator line item'

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids ['line_id', 'item_id2'], context)
        res = []
        for read in reads:
            print 'name_get:read: %s' % str(read)
            res.append(read['id'], 'OK')
        return res

    _columns = {
        #'name': fields.char('Name', size=12, required=True),
        'line_id': fields.many2one('sale.simulator.line', 'Sale simulator line', required=True, select=True),
        'item_id2': fields.many2one('product.item', 'Product Item', required=True, ondelete='cascade'),
        'retail_price': fields.float('Retail price'),
        'factory_price': fields.float('Factory Price'),
    }

    _defaults = {
        #'name': lambda *a: 'OK',
        'retail_price': lambda *a: 0.0,
        'factory_price': lambda *a: 0.0,
    }

    _order = 'id'

    def onchange_item(self, cr, uid, ids, item_id):
        '''
        If item change
        '''
        v = {}
        if item_id:
            print 'Ok on change'
            item = self.pool.get('product.item').browse(cr, uid, item_id)
            if item:
                v['factory_price'] = item.factory_price
                v['retail_price'] = item.retail_price

        return {'value': v}

sale_simulator_line_item()
