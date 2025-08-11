from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    
    # Mapeamento de tabelas e campos para migração
    migrations = [
        {
            'relation_table': 'ordem_servico_rel_sale',
            'columns': ('sale_order_id', 'os_id'),
            'target_field': 'pedido_venda'
        },
        {
            'relation_table': 'mrp_rel_os',
            'columns': ('os_id', 'mrp_production_id'),
            'target_field': 'produtos'
        },
        {
            'relation_table': 'hr_attendance_os_rel',
            'columns': ('hr_attendance_id', 'ordem_servico_id'),
            'target_field': 'apontamento'
        }
    ]
    
    for migration in migrations:
        if openupgrade.table_exists(cr, migration['relation_table']):
            cr.execute("""
                SELECT %s, %s
                FROM %s
            """ % (migration['columns'][0], migration['columns'][1], 
                  migration['relation_table']))
            for rel in cr.fetchall():
                cr.execute("""
                    UPDATE ordem_servico
                    SET %s = %%s
                    WHERE id = %%s
                """ % migration['target_field'], (rel[0], rel[1]))