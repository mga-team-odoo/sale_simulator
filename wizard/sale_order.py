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

