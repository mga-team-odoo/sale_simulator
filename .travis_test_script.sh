#!/usr/bin/env bash

cd ../server
ADDONS=sale_simulator

./openerp-server --db_user=openerp --db_password=mirounga --db_host=localhost --test-enable --stop-after-init --no-xmlrpc --no-xmlrpcs --no-netrpc --addons-path=../openerp-addons-ci,../web/addons -i $ADDONS -d ocb-mirounga > >(tee stdout.log)

if $(grep -v mail stdout.log | grep -q ERROR)
then
exit 1
else
exit 0
fi
