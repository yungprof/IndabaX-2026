# Introduction to SQL and Relational Databases
### GDSS Workshop — Day 2

This folder contains all materials for Day 1 of the GDSS SQL workshop. The session runs for 3 hours and covers the foundations of relational databases and SQL using PostgreSQL. It is designed to flow directly into Day 2: *Data Transformation, Manipulation, and Preparation in SQL*.

---

## Contents

| File | Description |
|---|---|
| `shopdb_workshop.sql` | Complete SQL script for the session — table setup, all teaching queries, exercises, and Day 2 preview queries |
| `SQL_Session_Outline.docx` | Detailed session outline with timings, module breakdown, and learning outcomes |
| `SQL_Facilitation_Presentation.pptx` | Facilitation PowerPoint presentation slides including basic definitions, exercises, and facilitation notes |
| `README.md` | This file |

---

## Session Overview

**Duration:** 3 hours  
**Level:** Beginner  
**Tool:** PostgreSQL 18 (pgAdmin)  
**Database:** `shopdb` — a fictional e-commerce store with 4 tables

| Time | Module |
|---|---|
| 0:00 – 0:15 | Welcome, Setup & Icebreaker |
| 0:15 – 0:45 | Module 1 — Relational Databases & Data Organisation |
| 0:45 – 1:15 | Module 2 — Tables, Data Types & Schema Design |
| 1:15 – 1:30 | Break |
| 1:30 – 2:10 | Module 3 — Introduction to SQL Queries |
| 2:10 – 2:40 | Module 4 — Query Style, Distinct, Aliasing & SQL Flavours |
| 2:40 – 2:55 | Module 5 — Hands-On Practice |
| 2:55 – 3:00 | Day 2 Preview & Close |

---

## The Workshop Dataset

The SQL script creates a database called `shopdb` with four tables:

```
customers ──< orders ──< order_items >── products
```

- **customers** — registered customers
- **products** — spanning Electronics, Accessories, and Furniture
- **orders** — orders with statuses: pending, shipped, delivered, cancelled
- **order_items** — linking orders to products (many-to-many)

---

## Learning Outcomes

By the end of this session, participants will be able to:

- Explain what a relational database is and how tables relate through keys
- Read a table schema and identify column types and constraints
- Explain the difference between primary keys and foreign keys
- Understand why NULL is not the same as zero or an empty string
- Write `SELECT` queries with `WHERE`, `ORDER BY`, `LIMIT`, and `OFFSET`
- Filter data using `=`, `!=`, `>`, `<`, `BETWEEN`, `IN`, `LIKE`, `ILIKE`, `IS NULL.`
- Combine filter conditions with `AND`, `OR`, and parentheses
- Remove duplicate results using `DISTINCT.`
- Rename columns and tables using aliases (`AS`)
- Write well-formatted, commented SQL
- Understand that SQL syntax varies across platforms (PostgreSQL, MySQL, BigQuery)

---

## 📫 Facilitators
**Eric Inkoom Ayitey**  
📧 [Email](mailto:ericinkoomayitey@gmail.com)  
🌍 [LinkedIn](https://www.linkedin.com/in/eric-inkoom-ayitey/)

**Anita Esi Eshun**  
📧 [Email](mailto:anitaeshun5@gmail.com)  
🌍 [LinkedIn](https://www.linkedin.com/in/anita-esi-eshun-4968141b1/)

---

*Day 1 of 2 — GDSS SQL Workshop*
