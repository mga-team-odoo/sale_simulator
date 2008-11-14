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

import pooler
import wizard
from tools.misc import UpdateableStr, UpdateableDict
import time

_select_form =  UpdateableStr() 
_select_fields = UpdateableDict()

def _pre_init(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    print 'data: %s' % str(data)

    # Recherche si un client est présent sur la fiche de simulation
    simul_obj = pool.get('sale.simulator')
    simul = simul_obj.read(cr, uid, data['id'], ['id','partner_id'], context)
    if not simul['partner_id']:
        raise wizard.except_wizard('Error','Select or create a partner!')

    # Composition du formulaire
    _select_form_list = [
        '<?xml version="1.0"?>',
        '<form string="Sale order">',
        '<separator string="Create a sale order based on configuration" colspan="4"/>',
    ]
    _select_form_list.append('<field name="simul" />')
    _select_form_list.append('</form>')
    _select_form.string = '\n'.join(_select_form_list)

    # Composition du champ
    _select_fields.clear()

    #recherche
    line_obj = pool.get('sale.simulator.line')
    args = [('simul_id','=',data['id'])]
    line_ids = line_obj.search(cr, uid, args)
    if not line_ids:
        raise wizard.except_wizard('Error', 'No line in simulation !')

    print 'line: %s' % str(line_ids)
    res = []
    for line_id in line_ids:
        line = line_obj.read(cr, uid, line_id, ['id','description'], context)
        print 'Line: %s' % str(line)
        res.append((line['id'], line['description']))
    print 'res: %s ' % str(res)

    # Composition
    _select_fields['simul'] = {
        'string': 'Line',
        'type': 'selection',
        'selection': res,
        'required': True,
    }
    
    return {}

def _make_order(self, cr, uid, data, context):
    '''
    When a configuration is selected, we can :
    - Create an order
    - Create a produit with this nomemclature
    '''
    print '_make_order: %s' % str(data)
    simul_nb = data['id']
    sline_nb = data['form']['simul']
    print '_make_order:simul_nb: %s' % str(simul_nb)
    pool = pooler.get_pool(cr.dbname)
    simul_obj = pool.get('sale.simulator')
    simul_line_obj = pool.get('sale.simulator.line')
    order_obj = pool.get('sale.order')
    order_line_obj = pool.get('sale.order.line')
    partner_obj = pool.get('res.partner')
    product_obj = pool.get('product.product')

    simul = simul_obj.read(cr, uid, simul_nb)
    if not simul:
        print '_make_order: Erreur lors de la recup de la simulation'

    # Récupération des addresses contact, livraison, facturation
    addr = partner_obj.address_get(cr, uid, [simul['partner_id'][0]],['delivery','invoice','contact'])
    print '_make_order:simul: %s' % str(simul)
    print '_make_order:addr:  %s' % str(addr)
    # Create an empty order
    order = {
        'origin': simul['name'],
        'date_order': time.strftime('%Y-%m-%d'),
        'partner_id': simul['partner_id'][0],
        'partner_invoice_id':addr['invoice'],
        'partner_order_id': addr['contact'],
        'partner_shipping_id': addr['delivery'],
        'pricelist_id': simul['pricelist_id'][0],
        'user_id': simul['user_id'][0],
        'shop_id': simul['shop_id'][0],
    }
    print 'order: %s' % str(order)
    # Création du devis,
    order_id = order_obj.create(cr, uid, order, context)
    if not order_id:
        print '_make_order: Erreur dans la création de l''entete du devis'

    # Ajout de cet ID sur la page de configuration en lien
    args = {'order_id': order_id}
    res = simul_line_obj.write(cr, uid, sline_nb, args, context)
    if not res:
        print '_make_order: Erreur lors de la MAJ du numéro de commande'

    # Création du produit
    # - Les taxes sont prises sur le produit de référence
    # - la catégorie aussi
    config = simul_line_obj.browse(cr, uid, sline_nb)
    if not config:
        print '_make_order: Erreur recherche produit'

    print '_make_order: config: %s' % str(config.description)
    print '_make_order: taxes: %s'% str(config.item_id.sale_taxes_id)

    taxes_ids = []
    for x in config.item_id.sale_taxes_id:
        taxes_ids.append(x.id)

    proref = {
        'name': config.description,
        'categ_id': config.item_id.categ_id.id,
        'taxes_id': [(6,0,taxes_ids)],
        'sale_ok': True,
        'purchase_ok': False,
        'list_price': config.sale_price,
        'standard_price': config.factory_price,
        'procure_method': 'make_to_order',
        'supply_method': 'produce',
    }
    print '_make_order:proref: %s' % str(proref)
    proref_id = product_obj.create(cr, uid, proref, context)
    if not proref_id:
        print '_make_order: erreur creation produit'

    # Création de la nomenclature principale
    

    # Ajout du produit sur le devis
    # TODO Unité à mettre sur l'item
    order_line = {
        'order_id': order_id,
        'name': config.description,
        'product_id': proref_id,
        'price_unit': config.sale_price,
        'tax_id': [(6,0,taxes_ids)],
        'type': 'make_to_order',
        'product_uom_qty': config.quantity,
        'product_uom': 1,
    }
    order_line_id = order_line_obj.create(cr, uid, order_line, context)
    if not order_line_id:
        print '_make_order: Erreur creation ligne de devis'

    return {}



class simul_create_order(wizard.interface):
    states = {
        'init': { 
            'actions': [_pre_init],
            'result': {
                'type': 'form',
                'arch': _select_form,
                'fields': _select_fields,
                'state': (
                    ('end','Cancel','gtk-cancel'),
                    ('created','Create','gtk-ok', True),
                )
            }
        },
        'created': {
            'actions': [_make_order],
            'result': {
                'type': 'state',
                'state': 'end',
            }
        }
    }

simul_create_order('simul.create_order')

