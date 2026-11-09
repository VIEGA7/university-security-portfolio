-- Reconstruction: employees columns transcribed from BSBD 8 / image3.png.
-- Other tables are a minimal NEW schema based on table names in the report.
USE PortfolioSecurityLab;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF SCHEMA_ID(N'lab') IS NOT NULL OR SCHEMA_ID(N'lab_private') IS NOT NULL
    THROW 50002, 'Lab schemas already exist. Refusing to overwrite them.', 1;
EXEC(N'CREATE SCHEMA lab AUTHORIZATION dbo');
EXEC(N'CREATE SCHEMA lab_private AUTHORIZATION dbo');

CREATE TABLE lab.employees (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(100) NOT NULL,
    position NVARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    department NVARCHAR(50) NOT NULL,
    salary DECIMAL(10,2) NOT NULL CHECK (salary >= 0)
);
CREATE TABLE lab.accounts (
    account_id INT IDENTITY PRIMARY KEY,
    account_name NVARCHAR(100) NOT NULL,
    balance DECIMAL(14,2) NOT NULL DEFAULT 0
);
CREATE TABLE lab.financial_transactions (
    transaction_id INT IDENTITY PRIMARY KEY,
    account_id INT NOT NULL REFERENCES lab.accounts(account_id),
    amount DECIMAL(14,2) NOT NULL,
    transaction_date DATE NOT NULL
);
CREATE TABLE lab.salary_reports (
    report_id INT IDENTITY PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES lab.employees(employee_id),
    report_month DATE NOT NULL,
    total DECIMAL(12,2) NOT NULL CHECK (total >= 0)
);
CREATE TABLE lab.tax_documents (
    document_id INT IDENTITY PRIMARY KEY,
    title NVARCHAR(100) NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0)
);
CREATE TABLE lab.categories (
    category_id INT IDENTITY PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE lab.products (
    product_id INT IDENTITY PRIMARY KEY,
    category_id INT NOT NULL REFERENCES lab.categories(category_id),
    name NVARCHAR(100) NOT NULL,
    price DECIMAL(12,2) NOT NULL CHECK (price >= 0)
);
CREATE TABLE lab.orders (
    order_id INT IDENTITY PRIMARY KEY,
    order_date DATE NOT NULL
);
CREATE TABLE lab.orderitems (
    orderitem_id INT IDENTITY PRIMARY KEY,
    order_id INT NOT NULL REFERENCES lab.orders(order_id),
    product_id INT NOT NULL REFERENCES lab.products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0)
);
CREATE TABLE lab_private.notes (note_id INT PRIMARY KEY, content NVARCHAR(100) NOT NULL);

INSERT INTO lab.employees(full_name, position, hire_date, department, salary) VALUES
 (N'Demo Employee A', N'Accountant', '2020-01-15', N'Finance', 120000),
 (N'Demo Employee B', N'Cashier', '2021-03-10', N'Cash', 45000);
INSERT INTO lab.accounts(account_name, balance) VALUES (N'Demo account', 100000);
INSERT INTO lab.financial_transactions(account_id, amount, transaction_date) VALUES (1, 5000, '2026-01-01');
INSERT INTO lab.salary_reports(employee_id, report_month, total) VALUES (1, '2026-01-01', 120000);
INSERT INTO lab.tax_documents(title, amount) VALUES (N'Demo tax', 1000);
INSERT INTO lab.categories(name) VALUES (N'Demo category');
INSERT INTO lab.products(category_id,name,price) VALUES (1,N'Demo product',100);
INSERT INTO lab.orders(order_date) VALUES ('2026-01-01');
INSERT INTO lab.orderitems(order_id,product_id,quantity) VALUES (1,1,2);
INSERT INTO lab_private.notes VALUES (1,N'Not available to accountants');
COMMIT;
GO
