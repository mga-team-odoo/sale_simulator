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
from openerp.tools.misc import UpdateableStr, UpdateableDict

import time

_select_form =  UpdateableStr()
_select_fields = UpdateableDict()

def _pre_init(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    print 'data: %s' % str(data)

    # Recherche si un client est présent sur la fiche de simulation
    simul_obj = pool['sale.simulator']
    simul = simul_obj.read(cr, uid, data['id'], ['id','partner_id'], context)
    if not simul['partner_id']:
        raise wizard.except_wizard('Error','Pour créer un devis, veuillez créer ou sélectionner un partenaire!')

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
    line_obj = pool['sale.simulator.line']
    args = [
        ('simul_id','=',data['id']),
        ('order_id','=',False),
    ]
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
    simul_nb = data['id']
    sline_nb = data['form']['simul']

    pool = pooler.get_pool(cr.dbname)
    simul_obj = pool['sale.simulator']
    simul_line_obj = pool['sale.simulator.line']
    simul_line_item_obj = pool['sale.simulator.line.item']
    order_obj = pool['sale.order']
    order_line_obj = pool['sale.order.line']
    partner_obj = pool['res.partner']
    product_obj = pool['product.product']

    simul = simul_obj.read(cr, uid, simul_nb)
    if not simul:
        print '_make_order: Erreur lors de la recup de la simulation'

    # *********************************************************************
    #  Retrieve contact, delivery, invoice address
    # *********************************************************************
    addr = partner_obj.address_get(cr, uid, [simul['partner_id'][0]],['delivery','invoice','contact'])

    # *********************************************************************
    #  Verify if the max discount was not exceed
    # *********************************************************************
    config = simul_line_obj.browse(cr, uid, sline_nb)
    if not config:
        print 'make_product.generate: Erreur recherche produit'

    max_discount = 0
    partner = partner_obj.browse(cr, uid, simul['partner_id'][0])
    for categ_id in partner.category_id:
        print 'category: %s::%s -> %s' % (str(categ_id.id), categ_id.name, str(categ_id.discount))
        if categ_id.discount:
            if categ_id.discount > max_discount:
                max_discount = categ_id.discount

    if config.discount > max_discount:
        print 'config: %s' % str(config.discount)
        raise wizard.except_wizard('Error', 'Erreur remise maximale dépassée (%s) : maxi (%s)' % (str(config.discount), str(max_discount)))


    # *********************************************************************
    #  Create an empty order
    # *********************************************************************
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

    order_id = order_obj.create(cr, uid, order, context)
    if not order_id:
        print '_make_order: Erreur dans la création de l''entete du devis'

    # *********************************************************************
    # Add ID in simulation line
    # *********************************************************************
    args = {'order_id': order_id}
    res = simul_line_obj.write(cr, uid, sline_nb, args, context)
    if not res:
        print '_make_order: Erreur lors de la MAJ du numéro de commande'

    # *********************************************************************
    #  Product section
    # *********************************************************************
    note = ''
    notes = [config.item_id.notes]
    codes = [config.item_id.code]

    # *********************************************************************
    # Check if configuration have a multi level
    # *********************************************************************
    item_ids = simul_line_item_obj.search(cr, uid, [('line_id','=',sline_nb)])
    if not item_ids:
        raise wizard.except_wizard('Error', 'Problème récupération des IDS')

    item_rs = simul_line_item_obj.browse(cr, uid, item_ids)
    if not item_rs:
        raise wizard.except_wizard('Error', 'Erreur parcours des IDS')

    step2 = False
    for item in item_rs:
        if item.item_id2.sequence == 2:
            step2 = True
        print 'generate:level: %s' % item.item_id2.sequence
        notes.append(item.item_id2.notes)
        codes.append(item.item_id2.code)

    note = '\n'.join(notes)
    coder = '-'.join(codes)
    print 'Note finale: %s' % note
    # *********************************************************************
    #  Add taxes on main product
    # *********************************************************************
    taxes_ids = []
    for x in config.item_id.sale_taxes_id:
        taxes_ids.append(x.id)

    # *********************************************************************
    # Compose name of main product by concatenate product item ans
    # all module(s) item(s)
    # *********************************************************************
    if step2:
        proname = config.item_id.name
    else:
        proname = config.description

    # *********************************************************************
    #  Prepare the first product
    # *********************************************************************
    proref1 = {
        'name': proname,
        'categ_id': config.item_id.categ_id.id,
        'taxes_id': [(6,0,taxes_ids)],
        'sale_ok': True,
        'purchase_ok': False,
        'list_price': config.retail_price,
        'standard_price': config.factory_price,
        'procure_method': 'make_to_order',
        'supply_method': 'produce',
        'uom_id': config.item_id.uom_id.id,
        'description_sale': note,
    }
    if not step2:
        proref1['name'] = coder[:64]
    print '_make_order:proref: %s' % str(proref1)

    pil_obj = pool['product.item.line']
    niv1_lst = {}
    niv2_lst = {}

    # *********************************************************************
    #  Search all modules items which compose the main product
    # *********************************************************************
    nivref_args = [('item_id','=',config.item_id.id)]

    nivref_ids = pil_obj.search(cr, uid, nivref_args)
    if nivref_ids:
        for nivref_id in nivref_ids:
            nivref = pil_obj.read(cr, uid, nivref_id, ['product_id','quantity','uom_id'], context)
            niv1_lst[nivref['product_id'][0]] = (nivref['quantity'], nivref['uom_id'][0])

    for niv1 in item_rs:
        pil_args = [
            ('item_id','=', niv1.item_id2.id)
        ]
        pil_ids = pil_obj.search(cr, uid, pil_args)
        if pil_ids:
            for pil_id in pil_ids:
                pil = pil_obj.read(cr, uid, pil_id, ['product_id','quantity','uom_id'], context)

                p_id = pil['product_id'][0]
                if niv1.item_id2.sequence == 1:
                    if pil['product_id'][0] in niv1_lst:
                        niv1_lst[p_id] = (niv1_lst[p_id][0] + pil['quantity'], pil['uom_id'][0])
                    else:
                        niv1_lst[p_id] = (pil['quantity'], pil['uom_id'][0])
                else:
                    if pil['product_id'][0] in niv2_lst:
                        niv2_lst[p_id] = (niv2_lst[p_id][0] + pil['quantity'], pil['uom_id'][0])
                    else:
                        niv2_lst[p_id] = (pil['quantity'], pil['uom_id'][0])

    print 'niv1_lst: %s' % str(niv1_lst)
    print 'niv2_lst: %s' % str(niv2_lst)

    #
    #  Create the first product.
    #
    proref_id1 = product_obj.create(cr, uid, proref1, context)
    if not proref_id1:
        print '_make_order: erreur creation produit'

    # *********************************************************************
    #  Add BOM on the main product.
    # *********************************************************************
    bom_obj = pool['mrp.bom']

    proref_bom1 = {
        'name': proname,
        'product_id': proref_id1,
        'product_qty': 1,
        'product_uom': config.item_id.uom_id.id,
    }
    prb1_id = bom_obj.create(cr, uid, proref_bom1, context)
    if not prb1_id:
        print 'erreur lors de la création de la BOM principale'

    for bom1 in niv1_lst:
        if niv1_lst[bom1][0] > 0:
            # le nombre de produit est supérieur a 0 donc on peut les ajoutés.
            print 'produit: %s:%s' % (str(bom1),str(niv1_lst[bom1]))
            # Recherche du nom du produit a mettre dans la bom
            propro = product_obj.read(cr, uid, bom1, ['name'], context)
            mod_bom1 = {
                'name': propro['name'],
                'product_id': bom1,
                'product_qty': niv1_lst[bom1][0],
                'product_uom': niv1_lst[bom1][1],
                'bom_id': prb1_id,
            }
            mod1_id = bom_obj.create(cr, uid, mod_bom1, context)
            if not mod1_id:
                print 'Erreur création produit %s ' % str(bom1)

    # *********************************************************************
    # Create product if an item module have 2 step
    # *********************************************************************
    if step2:
        proref2 = {
            'name': coder[:64],
            'categ_id': config.item_id.categ_id.id,
            'taxes_id': [(6,0,taxes_ids)],
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': config.retail_price,
            'standard_price': config.factory_price,
            'procure_method': 'make_to_order',
            'supply_method': 'produce',
            'uom_id': config.item_id.uom_id.id,
            'description_sale': note,
        }
        print '_make_order:proref: %s' % str(proref2)
        proref_id2 = product_obj.create(cr, uid, proref2, context)
        if not proref_id2:
            print '_make_order: erreur creation produit'

        proref_bom2 = {
            'name': config.description,
            'product_id': proref_id2,
            'product_qty': 1,
            'product_uom': config.item_id.uom_id.id,
        }
        prb2_id = bom_obj.create(cr, uid, proref_bom2, context)
        if not prb2_id:
            print 'erreur lors de la création de la BOM principale'

        #Ratache le produit N°1 en nomenclature en premier
        propro = product_obj.read(cr, uid, proref_id1, ['name'], context)
        mod_bomX = {
            'name': propro['name'],
            'product_id': proref_id1,
            'product_qty': niv1_lst[bom1][0],
            'product_uom': niv1_lst[bom1][1],
            'bom_id': prb2_id,
        }
        modx_id = bom_obj.create(cr, uid, mod_bomX, context)
        if not modx_id:
            print 'Erreur création produit %s ' % str(bom1)
        print 'ratache'

        # *****************************************************************
        #  Add all modules items in second step.
        # *****************************************************************
        for bom2 in niv2_lst:
            if niv2_lst[bom2][0] > 0:
                # le nombre de produit est supérieur a 0 donc on peut les ajoutés.
                print 'produit: %s:%s' % (str(bom2),str(niv2_lst[bom2]))
                # Recherche du nom du produit a mettre dans la bom
                propro = product_obj.read(cr, uid, bom2, ['name'], context)
                mod_bom1 = {
                    'name': propro['name'],
                    'product_id': bom2,
                    'product_qty': niv2_lst[bom2][0],
                    'product_uom': niv2_lst[bom2][1],
                    'bom_id': prb2_id,
                }
                mod2_id = bom_obj.create(cr, uid, mod_bom1, context)
                if not mod2_id:
                    print 'Erreur création produit %s ' % str(bom1)


    # *********************************************************************
    #  Remove after test
    # *********************************************************************
    #raise wizard.except_wizard('Error', 'STOP !')

    # *********************************************************************
    #  Add product on quotation.
    # *********************************************************************
    order_line = {
        'order_id': order_id,
        'name': coder[:64],
        'price_unit': config.sale_price,
        'tax_id': [(6,0,taxes_ids)],
        'type': 'make_to_order',
        'product_uom_qty': config.quantity,
        'product_uom': config.item_id.uom_id.id,
        'notes': note,
    }

    if step2:
        order_line['product_id'] = proref_id2
    else:
        order_line['product_id'] = proref_id1

    order_line_id = order_line_obj.create(cr, uid, order_line, context)
    if not order_line_id:
        raise wizard.except_wizard('Error', 'Error on create ligne order !')

    #raise wizard.except_wizard('Error', 'On stop')

    return {}



#
#
# MIGRATION: rewrite wizard.interface to osv.TransientModel
#
# MIGRATION: rewrite wizard.interface to osv.TransientModel
#
#
# MIGRATION: rewrite wizard.interface to osv.TransientModel
#
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

