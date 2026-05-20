-- ============================================
-- 5. ПРИМЕРЫ ЗАПРОСОВ
-- ============================================

-- --------------------------------------------------
-- 5.1. Получение дерева иерархии (рекурсивное CTE)
-- --------------------------------------------------
WITH RECURSIVE tree AS (
    SELECT id, name, folder_type, parent_id, 1 as level
    FROM folders WHERE parent_id IS NULL
    UNION ALL
    SELECT f.id, f.name, f.field_type, f.parent_id, t.level + 1
    FROM folders f
    JOIN tree t ON f.parent_id = t.id
)
SELECT id, name, folder_type, level FROM tree ORDER BY level, id;

-- --------------------------------------------------
-- 5.2. Получение документа (Договор) с данными из наследника
-- --------------------------------------------------
SELECT 
    d.id, d.version, d.title, d.author, d.created_date,
    c.contract_number, c.amount, c.counterparty, c.valid_from, c.valid_to,
    d.is_current, d.created_at
FROM documents d
JOIN contracts c ON d.id = c.document_id AND d.version = c.version
WHERE d.id = 1 AND d.is_current = TRUE;

-- --------------------------------------------------
-- 5.3. Получение истории версий документа
-- --------------------------------------------------
SELECT 
    d.version, d.title, d.content, d.author, d.created_at, d.is_current,
    c.contract_number, c.amount, c.counterparty
FROM documents d
LEFT JOIN contracts c ON d.id = c.document_id AND d.version = c.version
WHERE d.id = 1
ORDER BY d.version DESC;

-- --------------------------------------------------
-- 5.4. Получение всех актуальных договоров
-- --------------------------------------------------
SELECT 
    d.id, d.title, d.author, d.created_date,
    c.contract_number, c.amount, c.counterparty
FROM documents d
JOIN contracts c ON d.id = c.document_id AND d.version = c.version
WHERE d.is_current = TRUE AND d.doc_type = 'contract';

-- --------------------------------------------------
-- 5.5. Получение документов по папке (с иерархией)
-- --------------------------------------------------
SELECT d.id, d.title, d.doc_type, d.author, d.created_date
FROM documents d
WHERE d.folder_id IN (
    SELECT id FROM folders WHERE parent_id = 2 OR id = 2
) AND d.is_current = TRUE;

-- --------------------------------------------------
-- 5.6. Проверка работы триггера (версионирование)
-- --------------------------------------------------
-- Выводим все версии документа
SELECT id, version, title, is_current, created_at 
FROM documents 
WHERE id = 1 
ORDER BY version;