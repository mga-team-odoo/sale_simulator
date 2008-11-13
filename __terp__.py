# -*- coding: utf-8 -*-
{
    "name" : "Sale Simulator",
    "version" : "1.1",
    "author" : "Syleam Info Services",
    "website" : "http://www.syleam.fr/",
    "description": """
The sale simulator
    """,
    "category" : "Generic Modules/Sale",
    "depends" : [
        "base",
        "product",
        "sale",
    ],
    "init_xml" : [],
    "demo_xml" : [
        "sale_simulator_sequence.xml",
        "sale_simulator_demo.xml"
    ],
    "update_xml" : [
        "product_view.xml",
        "sale_view.xml",
        "sale_simulator_wizard.xml",
    ],
    "active": False,
    "installable": True,
}

