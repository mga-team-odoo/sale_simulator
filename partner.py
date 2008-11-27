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
# Add a control 
#
class res_partner_category(osv.osv):

    _inherit = 'res.partner.category'

    def _check_valid(self, cr, uid, ids):
        categories = self.browse(cr, uid, ids)
        for category in categories:
            if category.discount < 0 or category.discount > 100:
                return False
        return True

    _columns = {
        'discount': fields.float('Discount Control', required=True, help="If different to 0, there is a control when discount(%) is more important than this value")
    }

    _constraints = [
        (_check_valid, 'Erreur la valeur doit etre comprise entre 0 et 100', ['discount'])
    ]

res_partner_category()

