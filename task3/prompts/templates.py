SCHEMA_CONTEXT = """
-- Drop tables safely (order + CASCADE matters)
DROP TABLE IF EXISTS orderdetails CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS offices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS productlines CASCADE;

-- Tables
CREATE TABLE productlines (
  "productLine" VARCHAR(50) PRIMARY KEY,
  "textDescription" VARCHAR(4000),
  "htmlDescription" TEXT,
  "image" BYTEA
);

CREATE TABLE products (
  "productCode" VARCHAR(15) PRIMARY KEY,
  "productName" VARCHAR(70) NOT NULL,
  "productLine" VARCHAR(50) NOT NULL,
  "productScale" VARCHAR(10) NOT NULL,
  "productVendor" VARCHAR(50) NOT NULL,
  "productDescription" TEXT NOT NULL,
  "quantityInStock" INTEGER NOT NULL,
  "buyPrice" NUMERIC(10,2) NOT NULL,
  "MSRP" NUMERIC(10,2) NOT NULL,
  FOREIGN KEY ("productLine") REFERENCES productlines("productLine")
);

CREATE TABLE offices (
  "officeCode" VARCHAR(10) PRIMARY KEY,
  "city" VARCHAR(50) NOT NULL,
  "phone" VARCHAR(50) NOT NULL,
  "addressLine1" VARCHAR(50) NOT NULL,
  "addressLine2" VARCHAR(50),
  "state" VARCHAR(50),
  "country" VARCHAR(50) NOT NULL,
  "postalCode" VARCHAR(15) NOT NULL,
  "territory" VARCHAR(10) NOT NULL
);

CREATE TABLE employees (
  "employeeNumber" INTEGER PRIMARY KEY,
  "lastName" VARCHAR(50) NOT NULL,
  "firstName" VARCHAR(50) NOT NULL,
  "extension" VARCHAR(10) NOT NULL,
  "email" VARCHAR(100) NOT NULL,
  "officeCode" VARCHAR(10) NOT NULL,
  "reportsTo" INTEGER,
  "jobTitle" VARCHAR(50) NOT NULL,
  FOREIGN KEY ("reportsTo") REFERENCES employees("employeeNumber"),
  FOREIGN KEY ("officeCode") REFERENCES offices("officeCode")
);

CREATE TABLE customers (
  "customerNumber" INTEGER PRIMARY KEY,
  "customerName" VARCHAR(50) NOT NULL,
  "contactLastName" VARCHAR(50) NOT NULL,
  "contactFirstName" VARCHAR(50) NOT NULL,
  "phone" VARCHAR(50) NOT NULL,
  "addressLine1" VARCHAR(50) NOT NULL,
  "addressLine2" VARCHAR(50),
  "city" VARCHAR(50) NOT NULL,
  "state" VARCHAR(50),
  "postalCode" VARCHAR(15),
  "country" VARCHAR(50) NOT NULL,
  "salesRepEmployeeNumber" INTEGER,
  "creditLimit" NUMERIC(10,2),
  FOREIGN KEY ("salesRepEmployeeNumber") REFERENCES employees("employeeNumber")
);

CREATE TABLE payments (
  "customerNumber" INTEGER,
  "checkNumber" VARCHAR(50),
  "paymentDate" DATE NOT NULL,
  "amount" NUMERIC(10,2) NOT NULL,
  PRIMARY KEY ("customerNumber", "checkNumber"),
  FOREIGN KEY ("customerNumber") REFERENCES customers("customerNumber")
);

CREATE TABLE orders (
  "orderNumber" INTEGER PRIMARY KEY,
  "orderDate" DATE NOT NULL,
  "requiredDate" DATE NOT NULL,
  "shippedDate" DATE,
  "status" VARCHAR(15) NOT NULL,
  "comments" TEXT,
  "customerNumber" INTEGER NOT NULL,
  FOREIGN KEY ("customerNumber") REFERENCES customers("customerNumber")
);

CREATE TABLE orderdetails (
  "orderNumber" INTEGER,
  "productCode" VARCHAR(15),
  "quantityOrdered" INTEGER NOT NULL,
  "priceEach" NUMERIC(10,2) NOT NULL,
  "orderLineNumber" SMALLINT NOT NULL,
  PRIMARY KEY ("orderNumber", "productCode"),
  FOREIGN KEY ("orderNumber") REFERENCES orders("orderNumber"),
  FOREIGN KEY ("productCode") REFERENCES products("productCode")
);
"""

DECOMPOSITION_PROMPT = """
You are a SQL decomposition expert.
Analyze the following natural language query and extract a JSON object containing:
- "Intent": What is the user asking for?
- "Tables": Which tables from the database are needed? (Comma-separated)
- "Columns": Which columns are needed? (Comma-separated)
- "Filters": What are the filtering conditions (WHERE)? (None if not applicable)
- "Joins": What joins are needed? (None if not applicable)

Respond ONLY with valid JSON. Do not include markdown code blocks, just raw JSON.

Query: {question}
"""

GENERATION_PROMPT = """
You are an expert PostgreSQL developer. 
Using the database schema and the provided decomposition logic, write a highly optimized PostgreSQL SELECT query to answer the user's question.
Return ONLY the raw SQL string. Do not include markdown formatting, code blocks like ```sql, or explanations. 
Just the query starting with SELECT and ending with a semicolon. Ensure column and table names exactly match the schema including casing (using double quotes if needed).

Database Schema:
{schema}

Decomposition:
{decomposition}

User Question: {question}
"""

FIX_PROMPT = """
You are an expert PostgreSQL debugger. 
The following SQL query failed with an error when executed against the database.
Fix the SQL query based on the error message. 
Return ONLY the raw fixed SQL string. Do not include markdown formatting, code blocks like ```sql, or explanations.

Database Schema:
{schema}

Original Failed Query:
{failed_query}

Error Message:
{error_message}
"""
