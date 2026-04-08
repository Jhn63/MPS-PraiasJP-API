"""Seed EstacaoMonitoramento with João Pessoa beaches.

Revision ID: 001_seed_estacoes
Revises: 
Create Date: 2026-04-07 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001_seed_estacoes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert seed data for João Pessoa beaches."""
    # Define the beaches of João Pessoa with their monitoring status
    beaches = [
        {
            'nome': 'Praia de Tambaú',
            'localizacao': 'Tambaú, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'PROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia do Bessa',
            'localizacao': 'Bessa, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'IMPROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia de Manaíra',
            'localizacao': 'Manaíra, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'PROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia de Cabo Branco',
            'localizacao': 'Cabo Branco, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'PROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia de Jaguaribe',
            'localizacao': 'Jaguaribe, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'IMPROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia de Intermares',
            'localizacao': 'Intermares, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'PROPRIO',
            'dataInstall': datetime.utcnow()
        },
        {
            'nome': 'Praia de Jacaré',
            'localizacao': 'Jacaré, João Pessoa, PB',
            'status': 'ATUALIZADO',
            'baneabilidade': 'IMPROPRIO',
            'dataInstall': datetime.utcnow()
        },
    ]
    
    # Insert beaches into EstacaoMonitoramento table
    estacoes_table = sa.table(
        'EstacaoMonitoramento',
        sa.column('nome', sa.String),
        sa.column('localizacao', sa.String),
        sa.column('status', sa.String),
        sa.column('baneabilidade', sa.String),
        sa.column('dataInstall', sa.DateTime),
        sa.column('nivel_mare', sa.String)
    )
    
    for beach in beaches:
        insert_stmt = estacoes_table.insert().values(
            nome=beach['nome'],
            localizacao=beach['localizacao'],
            status=beach['status'],
            baneabilidade=beach['baneabilidade'],
            dataInstall=beach['dataInstall'],
            nivel_mare=None  # Will be populated by monitoring service
        )
        op.execute(insert_stmt)
    
    print(f"✓ Seeded {len(beaches)} beaches from João Pessoa")


def downgrade() -> None:
    """Remove seeded data (delete all beaches from João Pessoa)."""
    op.execute(
        "DELETE FROM EstacaoMonitoramento "
        "WHERE localizacao LIKE '%João Pessoa%' OR localizacao LIKE '%Tambaú%' OR "
        "localizacao LIKE '%Bessa%' OR localizacao LIKE '%Manaíra%' OR "
        "localizacao LIKE '%Cabo Branco%' OR localizacao LIKE '%Jaguaribe%' OR "
        "localizacao LIKE '%Intermares%' OR localizacao LIKE '%Jacaré%'"
    )
    print("✓ Removed seeded beaches from João Pessoa")
