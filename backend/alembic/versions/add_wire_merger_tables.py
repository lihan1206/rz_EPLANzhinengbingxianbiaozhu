"""
添加并线合并功能的数据库表

Revision ID: add_wire_merger_tables
Revises: 
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_wire_merger_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建 wire_merge_projects 表
    op.create_table(
        'wire_merge_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wire_merge_projects_id'), 'wire_merge_projects', ['id'], unique=False)
    
    # 创建 source_wires 表
    op.create_table(
        'source_wires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('wire_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('node_a', sa.String(length=100), nullable=False),
        sa.Column('node_b', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=50), nullable=False),
        sa.Column('cable_type', sa.String(length=50), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['wire_merge_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_wires_id'), 'source_wires', ['id'], unique=False)
    op.create_index(op.f('ix_source_wires_project_id'), 'source_wires', ['project_id'], unique=False)
    
    # 创建 merge_groups 表
    op.create_table(
        'merge_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=50), nullable=False),
        sa.Column('cable_type', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('wire_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['wire_merge_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_merge_groups_id'), 'merge_groups', ['id'], unique=False)
    op.create_index(op.f('ix_merge_groups_project_id'), 'merge_groups', ['project_id'], unique=False)
    
    # 创建 merge_group_wires 关联表
    op.create_table(
        'merge_group_wires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('wire_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['merge_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wire_id'], ['source_wires.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_merge_group_wires_group_id'), 'merge_group_wires', ['group_id'], unique=False)
    op.create_index(op.f('ix_merge_group_wires_id'), 'merge_group_wires', ['id'], unique=False)
    op.create_index(op.f('ix_merge_group_wires_wire_id'), 'merge_group_wires', ['wire_id'], unique=False)
    
    # 创建 wire_import_logs 表
    op.create_table(
        'wire_import_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('warning_count', sa.Integer(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['wire_merge_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wire_import_logs_id'), 'wire_import_logs', ['id'], unique=False)
    op.create_index(op.f('ix_wire_import_logs_project_id'), 'wire_import_logs', ['project_id'], unique=False)
    
    # 创建 merge_rule_configs 表
    op.create_table(
        'merge_rule_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('match_fields', sa.JSON(), nullable=True),
        sa.Column('auto_merge_rules', sa.JSON(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_merge_rule_configs_id'), 'merge_rule_configs', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_merge_rule_configs_id'), table_name='merge_rule_configs')
    op.drop_table('merge_rule_configs')
    op.drop_index(op.f('ix_wire_import_logs_project_id'), table_name='wire_import_logs')
    op.drop_index(op.f('ix_wire_import_logs_id'), table_name='wire_import_logs')
    op.drop_table('wire_import_logs')
    op.drop_index(op.f('ix_merge_group_wires_wire_id'), table_name='merge_group_wires')
    op.drop_index(op.f('ix_merge_group_wires_id'), table_name='merge_group_wires')
    op.drop_index(op.f('ix_merge_group_wires_group_id'), table_name='merge_group_wires')
    op.drop_table('merge_group_wires')
    op.drop_index(op.f('ix_merge_groups_project_id'), table_name='merge_groups')
    op.drop_index(op.f('ix_merge_groups_id'), table_name='merge_groups')
    op.drop_table('merge_groups')
    op.drop_index(op.f('ix_source_wires_project_id'), table_name='source_wires')
    op.drop_index(op.f('ix_source_wires_id'), table_name='source_wires')
    op.drop_table('source_wires')
    op.drop_index(op.f('ix_wire_merge_projects_id'), table_name='wire_merge_projects')
    op.drop_table('wire_merge_projects')
