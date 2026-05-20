import asyncpg
from typing import Optional, Dict, Any, List

class NativeDB:
    def __init__(self):
        self.dsn = "postgresql://postgres:12345@localhost/document_db"
    
    async def get_connection(self):
        return await asyncpg.connect(self.dsn)
    
    async def create_contract(self, data: Dict) -> Dict:
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "INSERT INTO documents (title, content, author, created_date, folder_id, doc_type, is_current) VALUES ($1,$2,$3,$4,$5,'contract',true) RETURNING id, version",
                    data['title'], data.get('content'), data['author'], data['created_date'], data['folder_id'])
                did, ver = row['id'], row['version']
                await conn.execute(
                    "INSERT INTO contracts (document_id, version, contract_number, amount, counterparty, valid_from, valid_to) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                    did, ver, data['contract_number'], data['amount'], data['counterparty'], data['valid_from'], data['valid_to'])
                return {"id": did, "version": ver}
        finally:
            await conn.close()
    
    async def create_invoice(self, data: Dict) -> Dict:
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "INSERT INTO documents (title, content, author, created_date, folder_id, doc_type, is_current) VALUES ($1,$2,$3,$4,$5,'invoice',true) RETURNING id, version",
                    data['title'], data.get('content'), data['author'], data['created_date'], data['folder_id'])
                did, ver = row['id'], row['version']
                await conn.execute(
                    "INSERT INTO invoices (document_id, version, invoice_number, amount, tax_rate, supplier, buyer) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                    did, ver, data['invoice_number'], data['amount'], data['tax_rate'], data['supplier'], data['buyer'])
                return {"id": did, "version": ver}
        finally:
            await conn.close()
    
    async def create_order(self, data: Dict) -> Dict:
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "INSERT INTO documents (title, content, author, created_date, folder_id, doc_type, is_current) VALUES ($1,$2,$3,$4,$5,'order',true) RETURNING id, version",
                    data['title'], data.get('content'), data['author'], data['created_date'], data['folder_id'])
                did, ver = row['id'], row['version']
                await conn.execute(
                    "INSERT INTO orders (document_id, version, order_number, order_type, responsible_person, execution_deadline) VALUES ($1,$2,$3,$4,$5,$6)",
                    did, ver, data['order_number'], data['order_type'], data['responsible_person'], data.get('execution_deadline'))
                return {"id": did, "version": ver}
        finally:
            await conn.close()
    
    async def update_document(self, doc_id: int, update_data: Dict) -> Dict:
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                set_clause = ", ".join([f"{k}=${i+2}" for i,k in enumerate(update_data.keys())])
                values = list(update_data.values())
                await conn.execute(f"UPDATE documents SET {set_clause} WHERE id=$1 AND is_current=true", doc_id, *values)
                new = await conn.fetchrow("SELECT id, version, is_current FROM documents WHERE id=$1 AND is_current=true", doc_id)
                return {"id": new['id'], "version": new['version'], "is_current": new['is_current']}
        finally:
            await conn.close()
    
    async def get_document_history(self, doc_id: int) -> List[Dict]:
        conn = await self.get_connection()
        try:
            rows = await conn.fetch(
                "SELECT d.*, c.contract_number, c.amount, c.counterparty, i.invoice_number, i.tax_rate, i.supplier, i.buyer, o.order_number, o.order_type, o.responsible_person FROM documents d LEFT JOIN contracts c ON d.id=c.document_id AND d.version=c.version LEFT JOIN invoices i ON d.id=i.document_id AND d.version=i.version LEFT JOIN orders o ON d.id=o.document_id AND d.version=o.version WHERE d.id=$1 ORDER BY d.version", doc_id)
            return [dict(r) for r in rows]
        finally:
            await conn.close()
    
    async def create_folder(self, name: str, folder_type: str, parent_id: Optional[int] = None) -> Dict:
        conn = await self.get_connection()
        try:
            row = await conn.fetchrow("INSERT INTO folders (name, folder_type, parent_id) VALUES ($1,$2,$3) RETURNING id, name, folder_type, parent_id, created_at", name, folder_type, parent_id)
            return dict(row)
        finally:
            await conn.close()
    
    async def get_folder_tree(self, root_id: Optional[int] = None) -> List[Dict]:
        conn = await self.get_connection()
        try:
            if root_id:
                rows = await conn.fetch("WITH RECURSIVE tree AS (SELECT id, name, folder_type, parent_id, 1 as level FROM folders WHERE id=$1 UNION ALL SELECT f.id, f.name, f.folder_type, f.parent_id, t.level+1 FROM folders f JOIN tree t ON f.parent_id=t.id) SELECT id, name, folder_type, parent_id, level FROM tree ORDER BY level, id", root_id)
            else:
                rows = await conn.fetch("WITH RECURSIVE tree AS (SELECT id, name, folder_type, parent_id, 1 as level FROM folders WHERE parent_id IS NULL UNION ALL SELECT f.id, f.name, f.folder_type, f.parent_id, t.level+1 FROM folders f JOIN tree t ON f.parent_id=t.id) SELECT id, name, folder_type, parent_id, level FROM tree ORDER BY level, id")
            return [dict(r) for r in rows]
        finally:
            await conn.close()
    
    async def delete_document_logical(self, doc_id: int) -> Dict:
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                await conn.execute("UPDATE documents SET is_current=false WHERE id=$1 AND is_current=true", doc_id)
                return {"id": doc_id, "deleted": True}
        finally:
            await conn.close()
    
    async def get_contract_by_id(self, doc_id: int) -> Optional[Dict]:
        conn = await self.get_connection()
        try:
            row = await conn.fetchrow("SELECT d.*, c.* FROM documents d JOIN contracts c ON d.id=c.document_id AND d.version=c.version WHERE d.id=$1 AND d.is_current=true", doc_id)
            return dict(row) if row else None
        finally:
            await conn.close()