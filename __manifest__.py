# Copyright 2022 Madureira Ind. e Com.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Ordem de Servico',
    'description': """
        Ordem de Serviço""",
    'version': '16.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Madureira Ind. e Com.',
    'website': 'www.madureira.ind.br',
    'depends': [
        'hr_attendance',
        'hr',
        'base',
        'sale',
        'sale_order_revision',
        'sale_order_general_discount',
        'sale_discount_display_amount',
        'sale_last_price_info',
        'sale_mrp',
        'stock',
        'mrp',
        'mgmtsystem',
        'product_dimension',
        'purchase',
        'purchase_stock',
        'purchase_discount',
        'purchase_last_price_info',
        'purchase_product_matrix',


    ],
    'data': [
        'security/ordem_servico.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/account.xml',
        'views/fechamento.xml',
        'views/hr.xml',
        # 'views/horas.xml',
        'views/inspecoes.xml',
        'views/l10n_br.xml',
        'views/menus.xml',
        'views/mgmtsystem.xml',
        'views/mrp.xml',
        'views/movimentacoes.xml',
        'views/ordem_servico.xml',
        'views/products.xml',
        'views/purchase.xml',
        'views/res_config_settings_view.xml',
        'views/sale.xml',
        'views/stock.xml',
        'report/capa.xml',
        'report/external_layout_boxed.xml',
        'report/inspecoes.xml',
        'report/mrporder.xml',
        'report/materiais.xml',
        'report/fechamento.xml',
        'report/sale.xml',
        'report/purchase.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ordem_servico/static/src/css/progress_bar_color.css',
            'ordem_servico/static/src/js/progress_bar_color.js',
            'static/src/js/progress_bar_color.js',

            ],
    },
    'demo': [
    ],
    "installable": True,
}
