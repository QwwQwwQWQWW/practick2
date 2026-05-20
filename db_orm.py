from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, TIMESTAMP, ForeignKey, select, and_, text
from datetime import datetime, date
from typing import Optional, Dict, Any, List

DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost/document_db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# ========== МОДЕЛИ ==========
class Folder(Base):
    __tablename__ = 'folders'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    folder_type = Column(String(50))
    parent_id = Column(Integer, ForeignKey('folders.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    version = Column(Integer, primary_key=True, default=1)
    title = Column(String(300))
    content = Column(String)
    author = Column(String(200))
    created_date = Column(Date)
    folder_id = Column(Integer, ForeignKey('folders.id'))
    doc_type = Column(String(50))
    is_current = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)

class Contract(Base):
    __tablename__ = 'contracts'
    document_id = Column(Integer, ForeignKey('documents.id'), primary_key=True)
    version = Column(Integer, ForeignKey('documents.version'), primary_key=True)
    contract_number = Column(String(100))
    amount = Column(Float)
    counterparty = Column(String(200))
    valid_from = Column(Date)
    valid_to = Column(Date)

class Invoice(Base):
    __tablename__ = 'invoices'
    document_id = Column(Integer, ForeignKey('documents.id'), primary_key=True)
    version = Column(Integer, ForeignKey('documents.version'), primary_key=True)
    invoice_number = Column(String(100))
    amount = Column(Float)
    tax_rate = Column(Float)
    supplier = Column(String(200))
    buyer = Column(String(200))

class Order(Base):
    __tablename__ = 'orders'
    document_id = Column(Integer, ForeignKey('documents.id'), primary_key=True)
    version = Column(Integer, ForeignKey('documents.version'), primary_key=True)
    order_number = Column(String(100))
    order_type = Column(String(50))
    responsible_person = Column(String(200))
    execution_deadline = Column(Date)

# ========== CRUD ОПЕРАЦИИ ==========

# --- ДОГОВОРЫ ---
async def create_contract(db: AsyncSession, data: Dict) -> Dict:
    doc = Document(
        title=data['title'], content=data.get('content'), author=data['author'],
        created_date=data['created_date'], folder_id=data['folder_id'], doc_type='contract', is_current=True
    )
    db.add(doc)
    await db.flush()
    
    contract = Contract(
        document_id=doc.id, version=doc.version, contract_number=data['contract_number'],
        amount=data['amount'], counterparty=data['counterparty'], valid_from=data['valid_from'], valid_to=data['valid_to']
    )
    db.add(contract)
    await db.commit()
    return {"id": doc.id, "version": doc.version}

async def get_contract_by_id(db: AsyncSession, doc_id: int) -> Optional[Dict]:
    result = await db.execute(
        select(Document, Contract)
        .join(Contract, and_(Document.id == Contract.document_id, Document.version == Contract.version))
        .where(Document.id == doc_id, Document.is_current == True)
    )
    row = result.first()
    if not row: return None
    doc, contract = row
    return {**{c.name: getattr(doc, c.name) for c in doc.__table__.columns},
            **{c.name: getattr(contract, c.name) for c in contract.__table__.columns}}

# --- СЧЁТА-ФАКТУРЫ ---
async def create_invoice(db: AsyncSession, data: Dict) -> Dict:
    doc = Document(
        title=data['title'], content=data.get('content'), author=data['author'],
        created_date=data['created_date'], folder_id=data['folder_id'], doc_type='invoice', is_current=True
    )
    db.add(doc)
    await db.flush()
    
    invoice = Invoice(
        document_id=doc.id, version=doc.version, invoice_number=data['invoice_number'],
        amount=data['amount'], tax_rate=data['tax_rate'], supplier=data['supplier'], buyer=data['buyer']
    )
    db.add(invoice)
    await db.commit()
    return {"id": doc.id, "version": doc.version}

# --- ПРИКАЗЫ ---
async def create_order(db: AsyncSession, data: Dict) -> Dict:
    doc = Document(
        title=data['title'], content=data.get('content'), author=data['author'],
        created_date=data['created_date'], folder_id=data['folder_id'], doc_type='order', is_current=True
    )
    db.add(doc)
    await db.flush()
    
    order = Order(
        document_id=doc.id, version=doc.version, order_number=data['order_number'],
        order_type=data['order_type'], responsible_person=data['responsible_person'], execution_deadline=data.get('execution_deadline')
    )
    db.add(order)
    await db.commit()
    return {"id": doc.id, "version": doc.version}

# --- ОБНОВЛЕНИЕ (создаёт новую версию) ---
async def update_document(db: AsyncSession, doc_id: int, update_data: Dict) -> Dict:
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_current == True)
    )
    doc = result.scalar_one()
    for key, value in update_data.items():
        if hasattr(doc, key):
            setattr(doc, key, value)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "version": doc.version, "is_current": doc.is_current}

# --- ИСТОРИЯ ВЕРСИЙ ---
async def get_document_history(db: AsyncSession, doc_id: int) -> List[Dict]:
    result = await db.execute(
        select(Document).where(Document.id == doc_id).order_by(Document.version)
    )
    docs = result.scalars().all()
    history = []
    for doc in docs:
        item = {"id": doc.id, "version": doc.version, "title": doc.title, "author": doc.author,
                "doc_type": doc.doc_type, "is_current": doc.is_current, "created_at": doc.created_at}
        if doc.doc_type == 'contract':
            r = await db.execute(select(Contract).where(Contract.document_id == doc.id, Contract.version == doc.version))
            c = r.scalar_one_or_none()
            if c:
                item['contract_number'] = c.contract_number
                item['amount'] = c.amount
                item['counterparty'] = c.counterparty
        elif doc.doc_type == 'invoice':
            r = await db.execute(select(Invoice).where(Invoice.document_id == doc.id, Invoice.version == doc.version))
            inv = r.scalar_one_or_none()
            if inv:
                item['invoice_number'] = inv.invoice_number
                item['amount'] = inv.amount
                item['tax_rate'] = inv.tax_rate
                item['supplier'] = inv.supplier
                item['buyer'] = inv.buyer
        elif doc.doc_type == 'order':
            r = await db.execute(select(Order).where(Order.document_id == doc.id, Order.version == doc.version))
            o = r.scalar_one_or_none()
            if o:
                item['order_number'] = o.order_number
                item['order_type'] = o.order_type
                item['responsible_person'] = o.responsible_person
        history.append(item)
    return history

# --- ИЕРАРХИЯ ---
async def create_folder(db: AsyncSession, name: str, folder_type: str, parent_id: Optional[int] = None) -> Dict:
    folder = Folder(name=name, folder_type=folder_type, parent_id=parent_id)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return {"id": folder.id, "name": folder.name, "folder_type": folder.folder_type, "parent_id": folder.parent_id}

async def get_folder_tree(db: AsyncSession, root_id: Optional[int] = None) -> List[Dict]:
    if root_id:
        query = text("""
            WITH RECURSIVE tree AS (
                SELECT id, name, folder_type, parent_id, 1 as level FROM folders WHERE id = :rid
                UNION ALL
                SELECT f.id, f.name, f.folder_type, f.parent_id, t.level + 1 FROM folders f
                JOIN tree t ON f.parent_id = t.id
            ) SELECT id, name, folder_type, parent_id, level FROM tree ORDER BY level, id
        """)
        result = await db.execute(query, {"rid": root_id})
    else:
        query = text("""
            WITH RECURSIVE tree AS (
                SELECT id, name, folder_type, parent_id, 1 as level FROM folders WHERE parent_id IS NULL
                UNION ALL
                SELECT f.id, f.name, f.folder_type, f.parent_id, t.level + 1 FROM folders f
                JOIN tree t ON f.parent_id = t.id
            ) SELECT id, name, folder_type, parent_id, level FROM tree ORDER BY level, id
        """)
        result = await db.execute(query)
    rows = result.fetchall()
    return [{"id": r[0], "name": r[1], "folder_type": r[2], "parent_id": r[3], "level": r[4]} for r in rows]

# --- ЛОГИЧЕСКОЕ УДАЛЕНИЕ ---
async def delete_document_logical(db: AsyncSession, doc_id: int) -> Dict:
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.is_current == True))
    doc = result.scalar_one_or_none()
    if not doc:
        return {"error": "Document not found"}
    doc.is_current = False
    db.add(doc)
    await db.commit()
    return {"id": doc_id, "deleted": True}

# --- СПИСКИ ---
async def get_all_contracts(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(Document, Contract)
        .join(Contract, and_(Document.id == Contract.document_id, Document.version == Contract.version))
        .where(Document.is_current == True, Document.doc_type == 'contract')
    )
    return [{"id": d.id, "title": d.title, "author": d.author, "contract_number": c.contract_number, "amount": c.amount} 
            for d, c in result.all()]

async def get_all_invoices(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(Document, Invoice)
        .join(Invoice, and_(Document.id == Invoice.document_id, Document.version == Invoice.version))
        .where(Document.is_current == True, Document.doc_type == 'invoice')
    )
    return [{"id": d.id, "title": d.title, "author": d.author, "invoice_number": i.invoice_number, "amount": i.amount} 
            for d, i in result.all()]

async def get_all_orders(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(Document, Order)
        .join(Order, and_(Document.id == Order.document_id, Document.version == Order.version))
        .where(Document.is_current == True, Document.doc_type == 'order')
    )
    return [{"id": d.id, "title": d.title, "author": d.author, "order_number": o.order_number, "order_type": o.order_type} 
            for d, o in result.all()]