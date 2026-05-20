from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uvicorn

from db_orm import AsyncSessionLocal
from db_orm import create_contract as orm_create_contract
from db_orm import create_invoice as orm_create_invoice
from db_orm import create_order as orm_create_order
from db_orm import get_contract_by_id as orm_get_contract
from db_orm import update_document as orm_update
from db_orm import get_document_history as orm_history
from db_orm import create_folder as orm_create_folder
from db_orm import get_folder_tree as orm_get_tree
from db_orm import delete_document_logical as orm_delete
from db_orm import get_all_contracts as orm_get_contracts

from db_native import NativeDB

from schemas import *

app = FastAPI(title="Система документооборота")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

USE_ORM = True
native_db = NativeDB()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ========== ИЕРАРХИЯ ==========
@app.post("/api/folders", response_model=FolderResponse)
async def create_folder(folder: FolderCreate, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_create_folder(db, folder.name, folder.folder_type, folder.parent_id)
    else:
        return await native_db.create_folder(folder.name, folder.folder_type, folder.parent_id)

@app.get("/api/folders/tree")
async def get_tree(root_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_get_tree(db, root_id)
    else:
        return await native_db.get_folder_tree(root_id)

# ========== ДОГОВОРЫ ==========
@app.post("/api/contracts", response_model=dict)
async def create_contract(contract: ContractCreate, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_create_contract(db, contract.dict())
    else:
        return await native_db.create_contract(contract.dict())

@app.get("/api/contracts/{doc_id}")
async def get_contract(doc_id: int, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        result = await orm_get_contract(db, doc_id)
    else:
        result = await native_db.get_contract_by_id(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contract not found")
    return result

@app.get("/api/contracts")
async def get_all_contracts(db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_get_contracts(db)
    else:
        return await native_db.get_all_contracts()

# ========== СЧЁТА-ФАКТУРЫ ==========
@app.post("/api/invoices", response_model=dict)
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_create_invoice(db, invoice.dict())
    else:
        return await native_db.create_invoice(invoice.dict())

# ========== ПРИКАЗЫ ==========
@app.post("/api/orders", response_model=dict)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_create_order(db, order.dict())
    else:
        return await native_db.create_order(order.dict())

# ========== ОБНОВЛЕНИЕ, ИСТОРИЯ, УДАЛЕНИЕ ==========
@app.put("/api/documents/{doc_id}")
async def update_document(doc_id: int, update_data: dict, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_update(db, doc_id, update_data)
    else:
        return await native_db.update_document(doc_id, update_data)

@app.get("/api/documents/{doc_id}/history")
async def get_history(doc_id: int, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_history(db, doc_id)
    else:
        return await native_db.get_document_history(doc_id)

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    if USE_ORM:
        return await orm_delete(db, doc_id)
    else:
        return await native_db.delete_document_logical(doc_id)

@app.get("/api/mode")
async def get_mode():
    return {"mode": "ORM (SQLAlchemy)" if USE_ORM else "Native SQL (asyncpg)"}

# ========== ВЕБ-ИНТЕРФЕЙС ==========
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)