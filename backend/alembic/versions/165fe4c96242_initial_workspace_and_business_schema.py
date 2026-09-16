"""Initial workspace and business schema"""

import sqlalchemy as sa

from alembic import op

revision = "165fe4c96242"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspaces",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_table(
        "people",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "role", sa.Enum("OWNER", "PARTNER", "WORKER", name="person_role"), nullable=False
        ),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("monthly_salary", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "(role = 'WORKER' AND monthly_salary IS NOT NULL AND monthly_salary > 0) OR (role != 'WORKER' AND monthly_salary IS NULL)",
            name="person_salary",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "id"),
    )
    op.create_index(op.f("ix_people_workspace_id"), "people", ["workspace_id"], unique=False)
    op.create_table(
        "projects",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "COMPLETED", name="project_status"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "id"),
    )
    op.create_index(op.f("ix_projects_workspace_id"), "projects", ["workspace_id"], unique=False)
    op.create_table(
        "advances",
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("paid_at", sa.Date(), nullable=False),
        sa.Column("salary_month", sa.Date(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("EXTRACT(DAY FROM salary_month) = 1", name="advance_month_start"),
        sa.CheckConstraint("amount > 0", name="advance_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id", "project_id"],
            ["projects.workspace_id", "projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "worker_id"],
            ["people.workspace_id", "people.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "advance_workspace_month", "advances", ["workspace_id", "salary_month"], unique=False
    )
    op.create_index(op.f("ix_advances_workspace_id"), "advances", ["workspace_id"], unique=False)
    op.create_table(
        "attendance",
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=2, scale=1), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("value IN (0.5, 1)", name="attendance_value"),
        sa.ForeignKeyConstraint(
            ["workspace_id", "person_id"],
            ["people.workspace_id", "people.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id", "work_date", name="attendance_person_date"),
    )
    op.create_index(
        "attendance_workspace_date", "attendance", ["workspace_id", "work_date"], unique=False
    )
    op.create_index(
        op.f("ix_attendance_workspace_id"), "attendance", ["workspace_id"], unique=False
    )
    op.create_table(
        "expenses",
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column(
            "category",
            sa.Enum("BUSINESS", "OWNER", "PARTNER", "OTHER", name="expense_category"),
            nullable=False,
        ),
        sa.Column("beneficiary_person_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "(category IN ('OWNER', 'PARTNER') AND beneficiary_person_id IS NOT NULL) OR (category IN ('BUSINESS', 'OTHER') AND beneficiary_person_id IS NULL)",
            name="expense_beneficiary",
        ),
        sa.CheckConstraint("amount > 0", name="expense_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id", "beneficiary_person_id"],
            ["people.workspace_id", "people.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "project_id"],
            ["projects.workspace_id", "projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "expense_workspace_date", "expenses", ["workspace_id", "expense_date"], unique=False
    )
    op.create_index(op.f("ix_expenses_workspace_id"), "expenses", ["workspace_id"], unique=False)
    op.create_table(
        "project_incomes",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("received_at", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("amount > 0", name="income_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id", "project_id"],
            ["projects.workspace_id", "projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "income_workspace_date", "project_incomes", ["workspace_id", "received_at"], unique=False
    )
    op.create_index(
        op.f("ix_project_incomes_workspace_id"), "project_incomes", ["workspace_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_project_incomes_workspace_id"), table_name="project_incomes")
    op.drop_index("income_workspace_date", table_name="project_incomes")
    op.drop_table("project_incomes")
    op.drop_index(op.f("ix_expenses_workspace_id"), table_name="expenses")
    op.drop_index("expense_workspace_date", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index(op.f("ix_attendance_workspace_id"), table_name="attendance")
    op.drop_index("attendance_workspace_date", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index(op.f("ix_advances_workspace_id"), table_name="advances")
    op.drop_index("advance_workspace_month", table_name="advances")
    op.drop_table("advances")
    op.drop_index(op.f("ix_projects_workspace_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_people_workspace_id"), table_name="people")
    op.drop_table("people")
    op.drop_table("workspaces")
    sa.Enum(name="expense_category").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="project_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="person_role").drop(op.get_bind(), checkfirst=True)
