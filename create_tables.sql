-- ============================================
-- СИСТЕМА ДОКУМЕНТООБОРОТА ОРГАНИЗАЦИИ
-- ============================================

-- 1. ИЕРАРХИЯ: отделы/папки
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    folder_type VARCHAR(50) NOT NULL, -- 'department', 'folder', 'subfolder'
    parent_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. НАСЛЕДОВАНИЕ: базовая таблица документов с версионированием
CREATE TABLE documents (
    id SERIAL,
    version INTEGER NOT NULL DEFAULT 1,
    title VARCHAR(300) NOT NULL,
    content TEXT,
    author VARCHAR(200) NOT NULL,
    created_date DATE NOT NULL,
    folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    doc_type VARCHAR(50) NOT NULL, -- 'contract', 'invoice', 'order'
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, version)
);

-- 3. НАСЛЕДНИК: Договор (Contract)
CREATE TABLE contracts (
    document_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    contract_number VARCHAR(100) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    counterparty VARCHAR(200) NOT NULL, -- контрагент
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    PRIMARY KEY (document_id, version),
    FOREIGN KEY (document_id, version) REFERENCES documents(id, version) ON DELETE CASCADE
);

-- 4. НАСЛЕДНИК: Счёт-фактура (Invoice)
CREATE TABLE invoices (
    document_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    invoice_number VARCHAR(100) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL,
    supplier VARCHAR(200) NOT NULL,
    buyer VARCHAR(200) NOT NULL,
    PRIMARY KEY (document_id, version),
    FOREIGN KEY (document_id, version) REFERENCES documents(id, version) ON DELETE CASCADE
);

-- 5. НАСЛЕДНИК: Приказ (Order)
CREATE TABLE orders (
    document_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    order_number VARCHAR(100) NOT NULL,
    order_type VARCHAR(50) NOT NULL, -- 'personnel', 'administrative', 'vacation'
    responsible_person VARCHAR(200) NOT NULL,
    execution_deadline DATE,
    PRIMARY KEY (document_id, version),
    FOREIGN KEY (document_id, version) REFERENCES documents(id, version) ON DELETE CASCADE
);

-- 6. Индексы
CREATE INDEX idx_folders_parent ON folders(parent_id);
CREATE INDEX idx_documents_current ON documents(is_current);
CREATE INDEX idx_documents_folder ON documents(folder_id);
CREATE INDEX idx_documents_type ON documents(doc_type);
CREATE INDEX idx_contracts_number ON contracts(contract_number);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_orders_number ON orders(order_number);