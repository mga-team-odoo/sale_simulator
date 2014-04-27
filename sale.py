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
import time


class sale_simulator(orm.Model):
    '''
    Sale simulator
    '''
    _name = 'sale.simulator'
    _description = 'Sale simulator'
    _order = 'name'

    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.id
        shop_ids = self.pool['sale.shop'].search(cr, uid, [('company_id', '=', company_id)], context=context)
        return shop_ids and shop_ids[0] or False

    _columns = {
        'name': fields.char('Simulation number', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', ondelete='cascade', required=True),
        'line_ids': fields.one2many('sale.simulator.line', 'simul_id', 'Lines', required=True),
        'user_id': fields.many2one('res.users', 'Salesman', required=True, help="Salesman user"),
        'shop_id': fields.many2one('sale.shop', 'Shop', required=True, help='Select shop to convert this sale as sale order'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool['ir.sequence'].get(cr, uid, 'sale.simulator'),
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'sale.simulator', context=c),
        'shop_id': _get_default_shop,
        'user_id': lambda obj, cr, uid, context: uid,
        'fiscal_position': False,
    }

    def onchange_partner(self, cr, uid, ids, partner_id, context=None):
        """
        Retrieve pricelist when select a partner
        """
        if context is None:
            context = {}

        res = {}
        if partner_id:
            partner = self.pool['res.partner'].browse(cr, uid, partner_id, context=context)
            if partner:
                res['pricelist_id'] = partner.property_product_pricelist and partner.property_product_pricelist.id or False
                res['fiscal_position'] = partner.property_account_position and partner.property_account_position.id or False

        return {'value': res}

    def copy(self, cr, uid, id, default=None, context=None):
        """
        When we duplicate the simulation, we just create a new number
        """
        if context is None:
            context = {}

        if default is None:
            default = {}

        default['name'] = self.pool['ir.sequence'].get(cr, uid, 'sale.simulator')
        return super(sale_simulator, self).copy(cr, uid, id, default, context=context)


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
        line_obj = self.pool['sale.simulator.line.item']
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
        line_obj = self.pool['sale.simulator.line.item']
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
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'sale.simulator', context=c),
        'quantity': 1.0,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        """
        We remove the sale order reference
        """
        if context is None:
            context = {}

        if default is None:
            default = {}

        default['order_id'] = False
        return super(sale_simulator_line, self).copy(cr, uid, id, default, context=context)

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def check_config(self, cr, uid, ids, context=None):
        '''
        Check if selected configuration is valid
        '''
        f_obj = self.pool['product.item.feature.line']
        sl_obj = self.pool['sale.simulator.line.item']
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
            product_item = self.pool['product.item'].browse(cr, uid, item_id)
            v['sale_price'] = product_item.retail_price
            if not name:
                v['description'] = product_item.name

        return {'value': v}

    def _compute_product_code(self, cr, uid, simul, context=None):
        """
        Compute the final product code from base element as prefix
        and each modules order by sequence
        """
        prefix = simul.item_id.code
        concat = ''
        for line in simul.line_ids:
            concat += line.item_id2.code
        return prefix + concat

    def _assembly_bom_from_line(self, cr, uid, line, context=None):
        """
        Retrieve all products to compose the BOM

        :param line: Browse record from the current line
        :type  line: openerp.osv.orm.browse
        :return: List of tuples
        :rtype: list
        """
        tmp_list = {}

        # first we retrieve module from base module
        for p in line.item_id.item_ids:
            if p.product_id.id in tmp_list.keys():
                tmp_list[p.product_id.id] = [tmp_list[p.product_id.id][0] + p.quantity, p.uom_id.id]
            else:
                tmp_list[p.product_id.id] = [p.quantity, p.uom_id.id]

        # Loop on all optional modules
        for opt in line.line_ids:
            for m in opt.item_id2.item_ids:
                if m.product_id.id in tmp_list.keys():
                    tmp_list[m.product_id.id] = [tmp_list[m.product_id.id][0] + m.quantity, m.uom_id.id]
                else:
                    tmp_list[m.product_id.id] = [m.quantity, m.uom_id.id]

        res = []
        for p_id in tmp_list:
            if tmp_list[p_id][0] > 0.0:
                res.append((p_id, tmp_list[p_id][0], tmp_list[p_id][1]))

        return res

    def create_product_with_bom(self, cr, uid, id, procode='', context=None):
        """
        Create the final product and BOM
        :param id: ID of the line
        :type  id: integer
        :param procode: Code of the final product
        :type  procode: str
        :return: ID of the final product
        :rtype: integer
        """
        product_obj = self.pool['product.product']
        product_ids = product_obj.search(cr, uid, [('default_code', '=', procode)], offset=0, limit=None, order=None, context=context)
        if product_ids:
            # The product already exists, we return the known id
            return product_ids[0]

        line = self.browse(cr, uid, id, context=context)
        final = {
            'name': line.description,
            'categ_id': line.item_id.categ_id.id,
            'taxes_id': [(6, 0, [t.id for t in line.item_id.sale_taxes_id])],
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': line.retail_price,
            'standard_price': line.factory_price,
            'procure_method': 'make_to_order',
            'supply_method': 'produce',
            'uom_id': line.item_id.uom_id.id,
            'uom_po_id': line.item_id.uom_id.id,
            'description_sale': line.item_id.notes,
            'type': 'product',
        }
        if line.item_id.company_id:
            final['company_id'] = line.item_id.company_id.id

        product_id = product_obj.create(cr, uid, final, context=context)
        bom = {
            'product_id': product_id,
            'product_qty': 1.0,
            'product_uom': line.item_id.uom_id.id,
            'type': line.item_id.bom_type == -1 and 'phantom' or 'normal',
            'routing_id': line.item_id.routing_id and line.item_id.routing_id.id or False,
            'bom_lines': [],
        }
        if line.item_id.company_id:
            bom['company_id'] = line.item_id.company_id.id

        # The assembly_bom_from_line return a list of tuple composed with
        # (product ID, Quantity, Unit of measure ID)
        for i in self._assembly_bom_from_line(cr, uid, line, context=context):
            bom['bom_lines'].append((0, 0, {
                'product_id': i[0],
                'product_qty': i[1],
                'product_uom': i[2],
            }))

        bom_id = self.pool['mrp.bom'].create(cr, uid, bom, context=context)

        # We supplier is specify we must create  an entry at the supplier form
        if line.item_id.supplier_id:
            supplier_form = {
                'name': line.item_id.supplier_id.id,
                'product_uom': line.item_id.uom_id.id,
            }
            product_obj.write(cr, uid, [product_id], {'seller_ids': [(0, 0, supplier_form)]}, context=context)

        return product_id

    def create_sale_order(self, cr, uid, ids, context=None):
        """
        Create the sale order and the product with the BOM structure
        """
        if len(ids) > 1:
            raise orm.except_orm(_('Error'), _('You can only create one sale order at the time!'))

        line = self.browse(cr, uid, ids[0], context=context)
        if not line:
            raise orm.except_orm(_('Error'), _('Line not found, please reload your browser!'))

        if not line.simul_id.partner_id:
            raise orm.except_orm(_('Error'), _('A partner is necessary before create a sale order!'))

        # Retrieve base module to check
        final_code = self._compute_product_code(cr, uid, line, context=context)

        # We create the product and BOM associated
        product_id = self.create_product_with_bom(cr, uid, ids[0], procode=final_code, context=context)

        # Search for invoicing and delevrey addresses
        addr = self.pool['res.partner'].address_get(cr, uid, [line.simul_id.partner_id.id], ['delivery', 'invoice', 'contact'], context=context)

        # retrieve fiscal position to compute
        fiscal_position = line.simul_id.fiscal_position
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position.id) or False

        # Create a sale order with one line included the final product
        sorder = {
            'origin': line.name,
            'date_order': time.strftime('%Y-%m-%d'),
            'partner_id': line.simul_id.partner_id.id,
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
            'pricelist_id': line.simul_id.pricelist_id.id,
            'user_id': line.simul_id.user_id.id,
            'shop_id': line.simul_id.shop_id.id,
            'fiscal_position': fiscal_position and fiscal_position.id or False,
            'order_line': [(0, 0,
                            {
                                'product_id': product_id,
                                'name': line.description,
                                'product_uom_qty': line.quantity,
                                'product_uom': line.item_id.uom_id.id,
                                'tax_id': [(6, 0, self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, line.item_id.sale_taxes_id))],
                                'price_unit': line.sale_price,
                            })],
        }

        order_id = self.pool['sale.order'].create(cr, uid, sorder, context=context)
        self.write(cr, uid, ids, {'order_id': order_id}, context=context)
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
        'company_id': lambda self, cr, uid, c: self.pool['res.company']._company_default_get(cr, uid, 'sale.simulator', context=c),
    }

    def onchange_item(self, cr, uid, ids, item_id, context=None):
        '''
        If item change, retrieve the factory and retail price
        '''
        if not item_id:
            return {}

        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)

        v = {}
        item = self.pool['product.item'].browse(cr, uid, item_id, context=context)
        if item:
            v.update({
                'factory_price': item.factory_price,
                'retail_price': item.retail_price,
            })

        return {'value': v}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
