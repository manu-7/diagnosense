"""init

Revision ID: 92b5f77319e7
Revises: 
Create Date: 2026-07-07 13:39:57.297308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '92b5f77319e7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('PATIENT', 'CENTER', 'ADMIN', name='userrole'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('reference_snippets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('parameter', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reference_snippets_parameter'), 'reference_snippets', ['parameter'], unique=False)
    op.create_table('diagnostic_centers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('center_name', sa.String(length=150), nullable=False),
    sa.Column('address', sa.String(length=300), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('license_number', sa.String(length=100), nullable=True),
    sa.Column('is_approved', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_diagnostic_centers_city'), 'diagnostic_centers', ['city'], unique=False)
    op.create_table('symptom_queries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=False),
    sa.Column('symptoms_text', sa.String(length=1000), nullable=False),
    sa.Column('recommended_package_ids', sa.JSON(), nullable=True),
    sa.Column('ai_reasoning', sa.String(length=2000), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_symptom_queries_patient_id'), 'symptom_queries', ['patient_id'], unique=False)
    op.create_table('packages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('center_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('symptom_tags', sa.String(length=500), nullable=True),
    sa.Column('test_type', sa.String(length=100), nullable=False),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['center_id'], ['diagnostic_centers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_packages_center_id'), 'packages', ['center_id'], unique=False)
    op.create_table('bookings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=False),
    sa.Column('center_id', sa.UUID(), nullable=False),
    sa.Column('package_id', sa.UUID(), nullable=False),
    sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('PENDING_PAYMENT', 'CONFIRMED', 'SAMPLE_COLLECTED', 'REPORT_READY', 'CANCELLED', name='bookingstatus'), nullable=False),
    sa.Column('razorpay_order_id', sa.String(length=100), nullable=True),
    sa.Column('razorpay_payment_id', sa.String(length=100), nullable=True),
    sa.Column('razorpay_signature', sa.String(length=255), nullable=True),
    sa.Column('payment_status', sa.Enum('PENDING', 'PAID', 'FAILED', 'REFUNDED', name='paymentstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['center_id'], ['diagnostic_centers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_center_id'), 'bookings', ['center_id'], unique=False)
    op.create_index(op.f('ix_bookings_patient_id'), 'bookings', ['patient_id'], unique=False)
    op.create_table('reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('booking_id', sa.UUID(), nullable=False),
    sa.Column('file_key', sa.String(length=500), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('extracted_values', sa.JSON(), nullable=True),
    sa.Column('anomalies', sa.JSON(), nullable=True),
    sa.Column('ai_explanation', sa.String(length=2000), nullable=True),
    sa.Column('explanation_sources', sa.JSON(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('booking_id')
    )
   


def downgrade() -> None:
    
    op.drop_table('reports')
    op.drop_index(op.f('ix_bookings_patient_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_center_id'), table_name='bookings')
    op.drop_table('bookings')
    op.drop_index(op.f('ix_packages_center_id'), table_name='packages')
    op.drop_table('packages')
    op.drop_index(op.f('ix_symptom_queries_patient_id'), table_name='symptom_queries')
    op.drop_table('symptom_queries')
    op.drop_index(op.f('ix_diagnostic_centers_city'), table_name='diagnostic_centers')
    op.drop_table('diagnostic_centers')
    op.drop_index(op.f('ix_reference_snippets_parameter'), table_name='reference_snippets')
    op.drop_table('reference_snippets')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    