USE PortfolioSecurityLab;
GO
SET NOCOUNT ON;
DECLARE @failures TABLE(test_name NVARCHAR(150));
EXECUTE AS USER = N'accountant_user';
BEGIN TRY
    -- Real allowed operation; not merely inspecting a role's name.
    SELECT employee_id, full_name, salary FROM lab.employees;
    SELECT transaction_id, amount FROM lab.financial_transactions;
    IF ISNULL(HAS_PERMS_BY_NAME(N'lab.employees',N'OBJECT',N'SELECT'),0) <> 1
        INSERT INTO @failures VALUES (N'Accountant must have SELECT');
    IF ISNULL(HAS_PERMS_BY_NAME(N'lab.employees',N'OBJECT',N'INSERT'),0) <> 0
        INSERT INTO @failures VALUES (N'Accountant must not INSERT');
    IF ISNULL(HAS_PERMS_BY_NAME(N'lab.employees',N'OBJECT',N'UPDATE'),0) <> 0
        INSERT INTO @failures VALUES (N'Accountant must not UPDATE');
    IF ISNULL(HAS_PERMS_BY_NAME(N'lab.employees',N'OBJECT',N'DELETE'),0) <> 0
        INSERT INTO @failures VALUES (N'Accountant must not DELETE');
    BEGIN TRY
        UPDATE lab.employees SET salary=salary WHERE employee_id=-1;
        INSERT INTO @failures VALUES (N'Actual UPDATE unexpectedly allowed');
    END TRY
    BEGIN CATCH
        IF ERROR_NUMBER() <> 229 THROW;
    END CATCH;
    BEGIN TRY
        DELETE FROM lab.employees WHERE employee_id=-1;
        INSERT INTO @failures VALUES (N'Actual DELETE unexpectedly allowed');
    END TRY
    BEGIN CATCH
        IF ERROR_NUMBER() <> 229 THROW;
    END CATCH;
    BEGIN TRY
        INSERT INTO lab.employees(full_name,position,hire_date,department,salary)
            SELECT N'Forbidden',N'Test','2026-01-01',N'Test',0 WHERE 1=0;
        INSERT INTO @failures VALUES (N'Actual INSERT unexpectedly allowed');
    END TRY
    BEGIN CATCH
        IF ERROR_NUMBER() <> 229 THROW;
    END CATCH;
    BEGIN TRY
        SELECT * FROM lab_private.notes;
        INSERT INTO @failures VALUES (N'Private schema unexpectedly readable');
    END TRY
    BEGIN CATCH
        IF ERROR_NUMBER() <> 229 THROW;
    END CATCH;
END TRY
BEGIN CATCH
    REVERT;
    THROW;
END CATCH;
REVERT;

EXECUTE AS USER = N'denied_reader';
BEGIN TRY
    BEGIN TRY
        SELECT * FROM lab.employees;
        INSERT INTO @failures VALUES (N'db_denydatareader unexpectedly allowed SELECT');
    END TRY
    BEGIN CATCH
        IF ERROR_NUMBER() <> 229 THROW;
    END CATCH;
END TRY
BEGIN CATCH
    REVERT;
    THROW;
END CATCH;
REVERT;
IF EXISTS (SELECT 1 FROM @failures)
BEGIN
    SELECT * FROM @failures;
    THROW 50003, 'Permissions verification failed.', 1;
END;
PRINT N'PASS: SELECT allowed; INSERT/UPDATE/DELETE and private SELECT denied; deny-reader checked.';
GO
