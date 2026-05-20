-- Функция версионирования для документов
CREATE OR REPLACE FUNCTION document_version_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.is_current = TRUE;
    UPDATE documents SET is_current = FALSE 
    WHERE id = OLD.id AND is_current = TRUE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер
DROP TRIGGER IF EXISTS trg_document_version ON documents;
CREATE TRIGGER trg_document_version
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION document_version_update();