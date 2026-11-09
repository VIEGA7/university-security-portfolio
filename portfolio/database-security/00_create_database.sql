-- Optional setup. Run separately as an administrator on YOUR local SQL Server.
-- Never execute the following lab against an existing university/production DB.
USE master;
GO
IF DB_ID(N'PortfolioSecurityLab') IS NOT NULL
    THROW 50001, 'PortfolioSecurityLab already exists. Inspect it; no objects were changed.', 1;
GO
CREATE DATABASE PortfolioSecurityLab;
GO
