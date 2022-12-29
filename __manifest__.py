# Copyright 2022 Madureira Ind. e Com.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Ordem de Servico',
    'description': """
        Ordem de Serviço""",
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Madureira Ind. e Com.',
    'website': 'www.madureira.ind.br',
    'depends': [
        'hr_attendance',
        'hr',
        'base',
        'sale',
        'stock',
        'mrp',
        'purchase',
        'purchase_stock',
        'l10n_br_fiscal',
    ],
    'data': [
        'security/ordem_servico.xml',
        'security/ir.model.access.csv',
        'views/ordem_fecha.xml',
        'views/extra_fields.xml',
        'views/inspecoes.xml',
        'views/menus.xml',
        'views/movimentacoes.xml',
        'views/ordem_servico.xml',
        'data/ir_sequence_data.xml',
        'report/capa.xml',
        'report/external_layout_boxed.xml',
    ],
    'demo': [
    ],
    "installable": True,
}
