# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Sylëam Info Services http://www.syleam.fr
#               All rights Reserved.
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


class res_partner_category(orm.Model):

    _inherit = 'res.partner.category'

    def _check_valid(self, cr, uid, ids, context=None):
        for category in self.browse(cr, uid, ids, context=context):
            if category.discount < 0 or category.discount > 100:
                return False
        return True

    _columns = {
        'discount': fields.float('Discount Control', required=True,
                                 help="If different to 0, it control max value"
                                 "of discount(%) and block if greather")
    }

    _defaults = {
        'discount': 0.0,
    }

    _constraints = [
        (_check_valid,
         'Erreur la valeur doit etre comprise entre 0 et 100',
         ['discount'])
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
