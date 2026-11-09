USE PortfolioSecurityLab;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;
CREATE ROLE accountant_role AUTHORIZATION dbo;
-- WITHOUT LOGIN makes this an isolated permissions demonstration, not server authentication.
CREATE USER accountant_user WITHOUT LOGIN;
ALTER ROLE accountant_role ADD MEMBER accountant_user;
GRANT SELECT ON SCHEMA::lab TO accountant_role;
DENY INSERT, UPDATE, DELETE ON SCHEMA::lab TO accountant_role;

CREATE USER denied_reader WITHOUT LOGIN;
ALTER ROLE db_denydatareader ADD MEMBER denied_reader;
COMMIT;
GO
-- The report's separate sysadmin login is deliberately not created here.
-- db_denydatareader does NOT constrain sysadmin; never combine them to enforce read denial.
