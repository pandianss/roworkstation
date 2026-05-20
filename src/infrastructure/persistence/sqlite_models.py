from __future__ import annotations

import uuid
from datetime import datetime, timezone

utc_now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Time, func
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    dept = Column(String)
    task_type = Column(String)
    priority = Column(String)
    due_date = Column(Date)
    due_time = Column(Time, nullable=True)
    assigned_to = Column(String)
    assigned_by = Column(String, nullable=True)
    status = Column(String, default="OPEN")
    source = Column(String)
    linked_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    snoozed_until = Column(Date, nullable=True)
    recurrence = Column(String, nullable=True)


class ReminderModel(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String)
    remind_at = Column(DateTime)
    channel = Column(String)
    sent = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)


class MISRecordModel(Base):
    __tablename__ = "mis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sol = Column(Integer, nullable=False, index=True)
    sb = Column(Float, default=0.0)
    cd = Column(Float, default=0.0)
    td = Column(Float, default=0.0)
    bulk_dep = Column(Float, default=0.0)
    rec_q1 = Column(Float, default=0.0)
    rec_q2 = Column(Float, default=0.0)
    rec_q3 = Column(Float, default=0.0)
    rec_q4 = Column(Float, default=0.0)
    cash_on_hand = Column(Float, default=0.0)
    atm_cash = Column(Float, default=0.0)
    bc_cash = Column(Float, default=0.0)
    bna_cash = Column(Float, default=0.0)
    crl = Column(Float, default=0.0)
    pl = Column(Float, default=0.0)
    npa = Column(Float, default=0.0)
    core_agri = Column(Float, default=0.0)
    gold = Column(Float, default=0.0)
    msme = Column(Float, default=0.0)
    housing = Column(Float, default=0.0)
    vehicle = Column(Float, default=0.0)
    personal = Column(Float, default=0.0)
    mortgage = Column(Float, default=0.0)
    education = Column(Float, default=0.0)
    liquirent = Column(Float, default=0.0)
    other_retail = Column(Float, default=0.0)
    mudra = Column(Float, default=0.0)
    agri_jl = Column(Float, default=0.0)
    retail_jl = Column(Float, default=0.0)
    shg = Column(Float, default=0.0)
    kcc = Column(Float, default=0.0)
    govt_spon = Column(Float, default=0.0)
    oth_schematic = Column(Float, default=0.0)
    total_retail = Column(Float, default=0.0)
    adv = Column(Float, default=0.0)


class IngestedFileModel(Base):
    __tablename__ = "ingested_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, unique=True, nullable=False)
    ingested_at = Column(DateTime, default=utc_now)


class MasterRecordModel(Base):
    __tablename__ = "masters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False, index=True)
    name_en = Column(String, nullable=False)
    name_hi = Column(String)
    name_local = Column(String)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(String)  # Store JSON as string
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class BudgetModel(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sol = Column(Integer, nullable=False, index=True)
    parameter = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    target = Column(Float, nullable=False)


class AdvancesRecordModel(Base):
    __tablename__ = "advances_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_dt = Column(Date, nullable=False, index=True)
    branch_code = Column(Integer, nullable=False, index=True)
    ac_name = Column(String)
    foracid = Column(String, index=True)
    schm_code = Column(String)
    gl_sub_cd = Column(String)
    open_dt = Column(Date)
    limit_cr = Column(Float)
    balance_cr = Column(Float)
    risk_category = Column(String, index=True)
    l1_category = Column(String)
    l2_sector = Column(String)
    l3_scheme = Column(String)
    priority_type = Column(String)

class MilestoneAchievementModel(Base):
    __tablename__ = 'milestone_achievements'
    
    id = Column(Integer, primary_key=True)
    sol = Column(Integer, nullable=False)
    branch_name = Column(String(100), nullable=False)
    parameter = Column(String(50), nullable=False)
    milestone = Column(String(20), nullable=False)
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())

class BranchVisitModel(Base):
    __tablename__ = "branch_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sol = Column(Integer, nullable=False, index=True)
    branch_name = Column(String, nullable=False)
    visit_date = Column(Date, nullable=False)
    visitor_name = Column(String, nullable=False)
    observations = Column(String)
    advice_to_branch = Column(String)
    reply_received = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class DICGCReturnModel(Base):
    __tablename__ = "dicgc_returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    half_year_ending = Column(Date, nullable=False)
    bank_code = Column(String)
    bank_name_address = Column(String)
    
    # Deposits (Items 1-3)
    total_deposits = Column(Float, default=0.0)
    foreign_govt_deposits = Column(Float, default=0.0)
    central_govt_deposits = Column(Float, default=0.0)
    state_govt_deposits = Column(Float, default=0.0)
    inter_bank_deposits = Column(Float, default=0.0)
    exempted_deposits = Column(Float, default=0.0)
    other_balances = Column(Float, default=0.0)
    assessable_deposits = Column(Float, default=0.0)
    
    # Other Reportable Items (Items 4-12)
    sundry_creditors = Column(Float, default=0.0)
    unpaid_dds = Column(Float, default=0.0)
    local_authorities = Column(Float, default=0.0)
    autonomous_bodies = Column(Float, default=0.0)
    security_deposits_govt = Column(Float, default=0.0)
    govt_embassy_officials = Column(Float, default=0.0)
    overdue_unclaimed = Column(Float, default=0.0)
    interest_accrued_payable = Column(Float, default=0.0)
    interest_accrued_all = Column(Float, default=0.0)
    
    # Premium & Tax (Items 4-9)
    premium_payable = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    penal_interest = Column(Float, default=0.0)
    credit_adjustment = Column(Float, default=0.0)
    debit_adjustment = Column(Float, default=0.0)
    debit_adjustment_date = Column(Date, nullable=True)
    penal_interest_debit = Column(Float, default=0.0)
    gst_debit_adjustment = Column(Float, default=0.0)
    net_amount_payable = Column(Float, default=0.0)
    
    # Breakup (Item 10) - Stored as JSON
    breakup_json = Column(String)
    sundry_summary_json = Column(String) # Format-I data
    
    # Comparison (Item 11-12)
    last_half_year_assessable = Column(Float, default=0.0)
    reason_for_decrease = Column(String)
    
    # Payment Details
    amount_paid = Column(Float, default=0.0)
    utr_no = Column(String)
    payment_mode = Column(String, default="RTGS/NEFT")
    payment_date = Column(Date, nullable=True)
    
    # Signatories
    place = Column(String)
    report_date = Column(Date)
    first_auth_name = Column(String)
    first_auth_desig = Column(String)
    second_auth_name = Column(String)
    second_auth_desig = Column(String)
    
    created_at = Column(DateTime, default=func.now())

class WizardSubmissionModel(Base):
    __tablename__ = "wizard_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wizard_type = Column(String, nullable=False, index=True)
    submitted_by = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    reference_no = Column(String, nullable=True)
    content_json = Column(String)  # Store form data as JSON
    created_at = Column(DateTime, default=func.now())
class CommunicationRequestModel(Base):
    __tablename__ = "communications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_unit = Column(String, nullable=False) # SOL or Branch Name
    sender_name = Column(String)
    receiver_dept = Column(String, nullable=False, index=True) # Target RO Dept
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, RESOLVED, CLOSED
    priority = Column(String, default="NORMAL")
    response_message = Column(String, nullable=True)
    responded_by = Column(String, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AccountOpeningModel(Base):
    __tablename__ = "account_openings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sol_id = Column(Integer, nullable=False, index=True)
    schm_type = Column(String, nullable=False, index=True)
    schm_code = Column(String, nullable=False)
    acct_opn_date = Column(Date, nullable=False, index=True)
    clr_bal_amt = Column(Float, default=0.0)
    average_balance = Column(Float, default=0.0)


class AccountClosureModel(Base):
    __tablename__ = "account_closures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sol_id = Column(Integer, nullable=False, index=True)
    acct_cls_date = Column(Date, nullable=False, index=True)
    schm_type = Column(String, nullable=False, index=True)

