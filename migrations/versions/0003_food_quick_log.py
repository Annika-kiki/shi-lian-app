"""Add foods and confirmed meals without modifying existing records."""
from alembic import op
from sqlalchemy import inspect
from backend.models.food import Food, ConfirmedMeal
revision = '0003'
down_revision = '0001'
branch_labels = ('food_quick_log',)
depends_on = None

def upgrade():
    bind = op.get_bind()
    for table in (Food.__table__, ConfirmedMeal.__table__):
        inspector = inspect(bind)
        if inspector.has_table(table.name):
            existing = {c['name']: c for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing:
                    raise RuntimeError(f'{table.name}缺少字段{column.name}，请人工检查兼容性')
                actual = existing[column.name]
                if actual['type']._type_affinity != column.type._type_affinity:
                    raise RuntimeError(f'{table.name}.{column.name}类型不兼容')
                if getattr(actual['type'], 'length', None) != getattr(column.type, 'length', None):
                    raise RuntimeError(f'{table.name}.{column.name}长度不兼容')
                if not column.nullable and actual['nullable']:
                    raise RuntimeError(f'{table.name}.{column.name}允许NULL，与新模型不兼容')
            if inspector.get_pk_constraint(table.name)['constrained_columns'] != ['id']:
                raise RuntimeError(f'{table.name}主键不兼容')
            if bind.dialect.name == 'mysql':
                options = inspector.get_table_options(table.name)
                if options.get('mysql_engine', '').lower() != 'innodb' or not options.get('mysql_collate', '').startswith('utf8mb4'):
                    raise RuntimeError(f'{table.name}必须使用InnoDB和utf8mb4')
            indexes = {tuple(i['column_names']) for i in inspector.get_indexes(table.name)}
            for index in table.indexes:
                if tuple(c.name for c in index.columns) not in indexes:
                    index.create(bind)
        else:
            table.create(bind)

def downgrade():
    raise RuntimeError('保留食物和饮食数据；不支持自动删除表')
