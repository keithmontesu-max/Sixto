"""Core data model — SIXTO ROOT X."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def now():
    return datetime.utcnow()


class Role(str, enum.Enum):
    OWNER = "OWNER"
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TECHNICIAN = "TECHNICIAN"
    CUSTOMER = "CUSTOMER"


class Classification(str, enum.Enum):
    ROOTABLE = "ROOTABLE"
    NOT_ROOTABLE = "NOT_ROOTABLE"
    BOOTLOADER_UNLOCKABLE = "BOOTLOADER_UNLOCKABLE"
    BOOTLOADER_LOCKED = "BOOTLOADER_LOCKED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNKNOWN = "UNKNOWN"
    EXCLUDED = "EXCLUDED"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    AWAITING_TECHNICIAN = "AWAITING_TECHNICIAN"
    TECHNICIAN_ASSIGNED = "TECHNICIAN_ASSIGNED"
    AWAITING_CUSTOMER = "AWAITING_CUSTOMER"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=Role.CUSTOMER.value, index=True)
    full_name: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str] = mapped_column(String(128), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # Notification preferences (non-essential respect)
    ntf_order: Mapped[bool] = mapped_column(Boolean, default=True)
    ntf_payment: Mapped[bool] = mapped_column(Boolean, default=True)
    ntf_promo: Mapped[bool] = mapped_column(Boolean, default=False)
    ntf_security: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (Index("ix_devices_user", "user_id"), Index("ix_devices_fp", "build_fingerprint"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    model_id: Mapped[str] = mapped_column(String(128), default="")
    hardware_variant: Mapped[str] = mapped_column(String(128), default="")
    chipset: Mapped[str] = mapped_column(String(64), default="")
    android_version: Mapped[str] = mapped_column(String(32), default="")
    kernel_version: Mapped[str] = mapped_column(String(128), default="")
    build_fingerprint: Mapped[str] = mapped_column(String(512), default="")
    bootloader_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    is_rooted: Mapped[bool] = mapped_column(Boolean, default=False)
    root_manager: Mapped[str] = mapped_column(String(32), default="")  # Magisk|KernelSU|APatch|""
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CompatibilityRecord(Base):
    """One record per exact model + hardware variant + firmware line."""
    __tablename__ = "compatibility_records"
    __table_args__ = (
        UniqueConstraint("manufacturer", "model", "hardware_variant", "firmware_line", name="uq_compat_device"),
        Index("ix_compat_lookup", "manufacturer", "model"),
        Index("ix_compat_approved", "is_approved"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), default="")
    hardware_variant: Mapped[str] = mapped_column(String(128), default="")
    chipset: Mapped[str] = mapped_column(String(64), default="")
    architecture: Mapped[str] = mapped_column(String(32), default="")
    android_version: Mapped[str] = mapped_column(String(32), default="")
    firmware_line: Mapped[str] = mapped_column(String(128), default="")  # build fingerprint prefix
    root_classification: Mapped[str] = mapped_column(String(32), default=Classification.UNKNOWN.value)
    bootloader_classification: Mapped[str] = mapped_column(String(32), default=Classification.UNKNOWN.value)
    root_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    unlock_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    supported_method: Mapped[str] = mapped_column(String(64), default="")  # e.g. Magisk|KernelSU|APatch
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    known_limitations: Mapped[list] = mapped_column(JSON, default=list)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str] = mapped_column(String(255), default="")
    last_tested_date: Mapped[str] = mapped_column(String(32), default="")
    release_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Service(Base):
    __tablename__ = "services"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(1000), default="")
    category: Mapped[str] = mapped_column(String(64), default="ROOT")
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="PHP")
    eta_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_root_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    refund_policy: Mapped[str] = mapped_column(String(1000), default="")
    terms: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Coupon(Base):
    """Promo codes — backend-only. Prices always come from server."""
    __tablename__ = "coupons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)  # fixed, if >0 wins
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=0)  # 0 = unlimited
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    min_order_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_user", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=True)
    technician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.PENDING.value, index=True)
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="PHP")
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    completion_report: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_order", "order_id"), Index("ix_payments_ref", "provider_ref"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="")  # GCASH|MAYA|CARD
    provider_ref: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="PHP")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING|PAID|FAILED|REFUNDED
    webhook_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_webhook: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SupportSession(Base):
    __tablename__ = "support_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    technician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="WAITING")  # WAITING|ACTIVE|EXPIRED|ENDED
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_actor", "actor_id"), Index("ix_audit_created", "created_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), default="")
    target_id: Mapped[str] = mapped_column(String(128), default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class DeviceOperation(Base):
    """One orchestrated device operation (root/bootloader/diagnostic).

    Typed + allowlisted only. No arbitrary shell. Each step has expected
    result + verification procedure. Destructive steps require explicit
    customer authorization recorded on the operation.
    """
    __tablename__ = "device_operations"
    __table_args__ = (Index("ix_ops_user", "user_id"), Index("ix_ops_order", "order_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    operation_type: Mapped[str] = mapped_column(String(32), default="ROOT")  # ROOT|BOOTLOADER|DIAGNOSTIC
    method: Mapped[str] = mapped_column(String(64), default="")  # Magisk|KernelSU|APatch
    status: Mapped[str] = mapped_column(String(32), default="PLANNED")  # PLANNED|AWAITING_AUTH|AUTHORIZED|EXECUTING|VERIFYING|COMPLETED|FAILED|CANCELLED
    steps: Mapped[list] = mapped_column(JSON, default=list)
    verification: Mapped[dict] = mapped_column(JSON, default=dict)
    failure_reason: Mapped[str] = mapped_column(String(1000), default="")
    authorized_by_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class SessionMessage(Base):
    __tablename__ = "session_messages"
    __table_args__ = (Index("ix_msgs_session", "session_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("support_sessions.id"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="text")  # text|status|consent|diag
    body: Mapped[str] = mapped_column(String(4000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notif_user", "user_id"), Index("ix_notif_read", "is_read"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), default="")
    body: Mapped[str] = mapped_column(String(1000), default="")
    kind: Mapped[str] = mapped_column(String(32), default="info")  # order|payment|session|update|security
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AppRelease(Base):
    __tablename__ = "app_releases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String(32), default="android")  # android|backend|compat
    version: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str] = mapped_column(String(4000), default="")
    signature_hash: Mapped[str] = mapped_column(String(256), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    rollout_percent: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class BugReport(Base):
    __tablename__ = "bug_reports"
    __table_args__ = (Index("ix_bugs_device", "device_id"), Index("ix_bugs_status", "status"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(String(4000), default="")
    severity: Mapped[str] = mapped_column(String(16), default="LOW")  # LOW|MED|HIGH|CRIT
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN|TRIAGED|FIXED|REGRESSION|CLOSED
    assignee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class BusinessConfig(Base):
    __tablename__ = "business_config"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class PushToken(Base):
    __tablename__ = "push_tokens"
    __table_args__ = (Index("ix_push_user", "user_id"), Index("ix_push_token", "token"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(16), default="android")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
