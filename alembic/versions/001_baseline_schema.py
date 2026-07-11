"""Baseline schema - all 8 tables from 3 services

Revision ID: 001_baseline
Revises: None
Create Date: 2026-07-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Service: feedback-service
    # Tables: alerts, feedback
    # ========================================================================

    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("wazuh_alert_id", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=True),
        sa.Column("dest_ip", sa.String(45), nullable=True),
        sa.Column("rule_id", sa.String(50), nullable=True),
        sa.Column("rule_description", sa.Text, nullable=True),
        sa.Column("rule_level", sa.Integer, nullable=True),
        sa.Column("raw_alert_json", JSONB, nullable=True),
        sa.Column("triage_result_json", JSONB, nullable=True),
        sa.Column("ai_severity", sa.String(20), nullable=True),
        sa.Column("ai_category", sa.String(50), nullable=True),
        sa.Column("ai_confidence", sa.Float, nullable=True),
        sa.Column("ai_is_true_positive", sa.Boolean, nullable=True),
        sa.Column("ml_prediction", sa.String(20), nullable=True),
        sa.Column("ml_confidence", sa.Float, nullable=True),
        sa.Column("organization_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("feedback_count", sa.Integer, server_default=sa.text("0")),
    )
    op.create_index("idx_alerts_source_ip", "alerts", ["source_ip"])
    op.create_index("idx_alerts_dest_ip", "alerts", ["dest_ip"])
    op.create_index("idx_alerts_ai_severity", "alerts", ["ai_severity"])
    op.create_index("idx_alerts_organization_id", "alerts", ["organization_id"])
    op.create_index("idx_alerts_created", "alerts", ["created_at"])

    op.create_table(
        "feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "alert_id",
            sa.String(255),
            sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("analyst_id", sa.String(100), nullable=False, index=True),
        sa.Column("true_severity", sa.String(20), nullable=True),
        sa.Column("true_category", sa.String(50), nullable=True),
        sa.Column("is_false_positive", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("true_label", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_feedback_fp", "feedback", ["is_false_positive"])

    # ========================================================================
    # Service: response-orchestrator
    # Tables: defense_plans, planned_actions, verification_results,
    #         defense_outcomes
    # ========================================================================

    op.create_table(
        "defense_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("incident_id", sa.String(255), nullable=False, index=True),
        sa.Column("simulation_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="triggered", index=True),
        sa.Column("incident_summary", sa.Text, nullable=True),
        sa.Column("detected_techniques", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("kill_chain_stage", sa.String(50), nullable=True),
        sa.Column("source_ips", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("dest_ips", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("pre_defense_risk", sa.Float, nullable=True),
        sa.Column("post_defense_risk", sa.Float, nullable=True),
        sa.Column("simulation_summary", JSONB, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("total_actions", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("auto_executed_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("human_approved_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("dry_run", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "planned_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "plan_id",
            sa.String(255),
            sa.ForeignKey("defense_plans.plan_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("action_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("target_hostname", sa.String(255), nullable=True),
        sa.Column("adapter", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("impact_score", sa.Float, nullable=False),
        sa.Column("safety_score", sa.Float, nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("blast_radius", sa.String(20), nullable=False),
        sa.Column("approval_tier", sa.Integer, nullable=False),
        sa.Column("requires_approval", sa.Boolean, nullable=False),
        sa.Column("d3fend_technique", sa.String(100), nullable=True),
        sa.Column("d3fend_label", sa.String(255), nullable=True),
        sa.Column("counters_techniques", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending", index=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adapter_response", JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approval_notes", sa.Text, nullable=True),
    )

    op.create_table(
        "verification_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "plan_id",
            sa.String(255),
            sa.ForeignKey("defense_plans.plan_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("pre_attack_success_rate", sa.Float, nullable=False),
        sa.Column("post_attack_success_rate", sa.Float, nullable=False),
        sa.Column("risk_reduction_pct", sa.Float, nullable=False),
        sa.Column("re_simulation_id", sa.String(255), nullable=True),
        sa.Column("continued_indicators", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("monitoring_duration_seconds", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("new_alerts_during_monitoring", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("verification_passed", sa.Boolean, nullable=False),
        sa.Column("verdict_reason", sa.Text, nullable=True),
    )

    op.create_table(
        "defense_outcomes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_id", sa.String(255), nullable=False, index=True),
        sa.Column("action_type", sa.String(50), nullable=False, index=True),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("countered_technique", sa.String(50), nullable=False, index=True),
        sa.Column("pre_risk", sa.Float, nullable=False),
        sa.Column("post_risk", sa.Float, nullable=False),
        sa.Column("risk_delta", sa.Float, nullable=False),
        sa.Column("was_effective", sa.Boolean, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ========================================================================
    # Service: correlation-engine
    # Tables: incidents, incident_alerts
    # ========================================================================

    op.create_table(
        "incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open", index=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("kill_chain_stage", sa.String(50), nullable=True),
        sa.Column("kill_chain_stages_seen", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("alert_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_ips", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("dest_ips", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("mitre_techniques", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("mitre_tactics", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_incidents_last_seen", "incidents", ["last_seen"])

    op.create_table(
        "incident_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "incident_id",
            sa.String(255),
            sa.ForeignKey("incidents.incident_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("alert_id", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("kill_chain_stage", sa.String(50), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("incident_alerts")
    op.drop_table("incidents")
    op.drop_table("defense_outcomes")
    op.drop_table("verification_results")
    op.drop_table("planned_actions")
    op.drop_table("defense_plans")
    op.drop_table("feedback")
    op.drop_table("alerts")
