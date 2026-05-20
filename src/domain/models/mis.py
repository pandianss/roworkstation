from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class MISRecord(BaseModel):
    id: Optional[int] = None
    date: date
    sol: int
    sb: float = 0.0
    cd: float = 0.0
    td: float = 0.0
    bulk_dep: float = 0.0
    rec_q1: float = 0.0
    rec_q2: float = 0.0
    rec_q3: float = 0.0
    rec_q4: float = 0.0
    cash_on_hand: float = 0.0
    atm_cash: float = 0.0
    bc_cash: float = 0.0
    bna_cash: float = 0.0
    crl: float = 0.0
    pl: float = 0.0
    npa: float = 0.0
    core_agri: float = 0.0
    gold: float = 0.0
    msme: float = 0.0
    housing: float = 0.0
    vehicle: float = 0.0
    personal: float = 0.0
    mortgage: float = 0.0
    education: float = 0.0
    liquirent: float = 0.0
    other_retail: float = 0.0
    kcc: float = 0.0
    shg: float = 0.0
    govt_spon: float = 0.0
    oth_schematic: float = 0.0
    retail_jl: float = 0.0
    agri_jl: float = 0.0
    mudra: float = 0.0

class IngestedFile(BaseModel):
    id: Optional[int] = None
    filename: str
    ingested_at: datetime = Field(default_factory=datetime.now)
