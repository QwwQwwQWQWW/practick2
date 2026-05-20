from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# ========== ИЕРАРХИЯ (ПАПКИ) ==========
class FolderCreate(BaseModel):
    name: str
    folder_type: str
    parent_id: Optional[int] = None

class FolderResponse(FolderCreate):
    id: int
    created_at: datetime

# ========== БАЗОВЫЙ ДОКУМЕНТ ==========
class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None
    author: str
    created_date: date
    folder_id: int

# ========== НАСЛЕДНИК: ДОГОВОР ==========
class ContractCreate(DocumentBase):
    contract_number: str
    amount: float
    counterparty: str
    valid_from: date
    valid_to: date

class ContractResponse(ContractCreate):
    id: int
    version: int
    is_current: bool
    created_at: datetime

# ========== НАСЛЕДНИК: СЧЁТ-ФАКТУРА ==========
class InvoiceCreate(DocumentBase):
    invoice_number: str
    amount: float
    tax_rate: float
    supplier: str
    buyer: str

class InvoiceResponse(InvoiceCreate):
    id: int
    version: int
    is_current: bool
    created_at: datetime

# ========== НАСЛЕДНИК: ПРИКАЗ ==========
class OrderCreate(DocumentBase):
    order_number: str
    order_type: str
    responsible_person: str
    execution_deadline: Optional[date] = None

class OrderResponse(OrderCreate):
    id: int
    version: int
    is_current: bool
    created_at: datetime

# ========== ИСТОРИЯ ВЕРСИЙ ==========
class DocumentHistoryResponse(BaseModel):
    id: int
    version: int
    title: str
    author: str
    doc_type: str
    is_current: bool
    created_at: datetime
    contract_number: Optional[str] = None
    amount: Optional[float] = None
    counterparty: Optional[str] = None
    invoice_number: Optional[str] = None
    tax_rate: Optional[float] = None
    supplier: Optional[str] = None
    buyer: Optional[str] = None
    order_number: Optional[str] = None
    order_type: Optional[str] = None
    responsible_person: Optional[str] = None