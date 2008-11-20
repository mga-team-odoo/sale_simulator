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
    print '_make_order: %s' % str(data)
    simul_nb = data['id']
    sline_nb = data['form']['simul']
    print '_make_order:simul_nb: %s' % str(simul_nb)
    pool = pooler.get_pool(cr.dbname)
    simul_obj = pool.get('sale.simulator')
    simul_line_obj = pool.get('sale.simulator.line')
    simul_line_item_obj = pool.get('sale.simulator.line.item')
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

    # Création des produits 
    # Création du produit assemblé de toutes les pièces
    # Création du produit, composé du produit précédent.
    # - Les taxes sont prises sur le produit de référence
    # - la catégorie aussi

    # proref_id = make_product.generate(cr, uid, sline_nb, context)
    # Search product and module items on this configuration
    config = simul_line_obj.browse(cr, uid, sline_nb)
    if not config:
        print 'make_product.generate: Erreur recherche produit'

    print '_make_order: config: %s' % str(config.description)
    print '_make_order: taxes: %s'% str(config.item_id.sale_taxes_id)

    # Check if configuration have a multi level
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

    #
    # Ajout des taxes principales du produits de base
    #
    taxes_ids = []
    for x in config.item_id.sale_taxes_id:
        taxes_ids.append(x.id)

    #
    # Choisit le nom du produit final en fonction du nombre de niveau
    #
    if step2:
        proname = config.item_id.name
    else:
        proname = config.description

    #
    # Création du produit (1)
    #
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
        'uom_id': config.item_id.uom_id.id
    }
    print '_make_order:proref: %s' % str(proref1)
    proref_id1 = product_obj.create(cr, uid, proref1, context)
    if not proref_id1:
        print '_make_order: erreur creation produit'

    #
    # Création de la nomemclature du produit de niveau 1
    #
    pil_obj = pool.get('product.item.line')
    niv1_lst = {}
    niv2_lst = {}

    # On recherche les produits qui compose le produit de référence
    nivref_args = [('item_id','=',config.item_id.id)]
    print 'nivref_args: %s' % str(nivref_args)

    nivref_ids = pil_obj.search(cr, uid, nivref_args)
    if nivref_ids:
        print 'AFF: nivref_ids: %s' % str(nivref_ids)
        for nivref_id in nivref_ids:
            nivref = pil_obj.read(cr, uid, nivref_id, ['product_id','quantity','uom_id'], context)
            print 'AFF: nivref: %s ' % str(nivref)
            niv1_lst[nivref['product_id'][0]] = (nivref['quantity'], nivref['uom_id'][0])

    for niv1 in item_rs:
        pil_args = [
            ('item_id','=', niv1.item_id2.id)
        ]
        pil_ids = pil_obj.search(cr, uid, pil_args)
        if pil_ids:
            for pil_id in pil_ids:
                pil = pil_obj.read(cr, uid, pil_id, ['product_id','quantity','uom_id'], context)
                print 'AFF: pil: %s' % str(pil)

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

    # Constitution de la nomemclature du premier produit.
    bom_obj = pool.get('mrp.bom')

    # le produit lui même a sa BOM
    # on récupère son id pour ses composants
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

    # si niveau 2 on créer le produit
    if step2:
        #print'****************** NIVEAU 2 ***************************'
        #Création du produit numéro 2
        proref2 = {
            'name': config.description,
            'categ_id': config.item_id.categ_id.id,
            'taxes_id': [(6,0,taxes_ids)],
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': config.retail_price,
            'standard_price': config.factory_price,
            'procure_method': 'make_to_order',
            'supply_method': 'produce',
            'uom_id': config.item_id.uom_id.id
        }
        print '_make_order:proref: %s' % str(proref2)
        proref_id2 = product_obj.create(cr, uid, proref2, context)
        if not proref_id2:
            print '_make_order: erreur creation produit'

        # le produit a lui même sa nomenclature

        proref_bom2 = {
            'name': config.description,
            'product_id': proref_id2,
            'product_qty': 1,
            'product_uom': config.item_id.uom_id.id,
        }
        prb2_id = bom_obj.create(cr, uid, proref_bom2, context)
        if not prb2_id:
            print 'erreur lors de la création de la BOM principale'
        #print '***************** BOM 2 CREER ********************'

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
        #On ratache les autres produits
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
    # A retirer après les tests
    # *********************************************************************
    #raise wizard.except_wizard('Error', 'STOP !')

    # Ajout du produit sur le devis
    # TODO Unité à mettre sur l'item
    order_line = {
        'order_id': order_id,
        'name': config.description,
        'price_unit': config.sale_price,
        'tax_id': [(6,0,taxes_ids)],
        'type': 'make_to_order',
        'product_uom_qty': config.quantity,
        'product_uom': config.item_id.uom_id.id,
    }

    if step2:
        order_line['product_id'] = proref_id2
    else:
        order_line['product_id'] = proref_id1

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

