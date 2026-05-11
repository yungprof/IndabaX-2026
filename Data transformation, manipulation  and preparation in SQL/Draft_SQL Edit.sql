--- GDSS DATA TRANSFROMATION Draft edited
---- 18th April, 2026
-- ============================================================
-- MODULE 1: EXPLORING DATA
-- Abena's brief: "Before you touch anything, tell me what we are working with."
-- ============================================================

-- 1a. Row counts for every table
SELECT 'distributors'   AS table_name, COUNT(*) AS row_count FROM distributors
UNION ALL
SELECT 'product_variants',              COUNT(*)             FROM product_variants
UNION ALL
SELECT 'orders',                        COUNT(*)             FROM orders
UNION ALL
SELECT 'delivery_dates',                COUNT(*)             FROM delivery_dates;


-- 1c. Profile nulls in the orders table
SELECT
    COUNT(*)                          AS total_rows,
    COUNT(distributor_id)             AS non_null_distributor_id,
    COUNT(variant_id)                 AS non_null_variant_id,
    --COUNT(quantity)                   AS non_null_quantity,
    COUNT(order_date)                 AS non_null_order_date,
    COUNT(region)                     AS non_null_region,
 --   COUNT(status)                     AS non_null_status,
    -- null counts derived from total - non_null
  --  COUNT(*) - COUNT(quantity)        AS null_quantity_count
FROM orders;

-- 1d. Quick distribution checks — min, max, avg quantity
SELECT
    MIN(quantity)  AS min_qty,
    MAX(quantity)  AS max_qty,
    ROUND(AVG(quantity), 2) AS avg_qty
FROM orders
WHERE quantity IS NOT NULL;

-- 1e. Spot duplicates in distributors by name (case-insensitive)
SELECT
    LOWER(TRIM(distributor_name)) AS cleaned_name,
    COUNT(*) AS occurrences
FROM distributors
GROUP BY LOWER(TRIM(distributor_name))
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;


-- ============================================================
-- MODULE 2: COLUMN TYPES, CONSTRAINTS & CASTING
-- Abena's brief: "Some quantities look off — flag anything suspicious."
-- ============================================================

-- 2a. Flag suspicious quantities (likely individual packs instead of cartons)
--     Assuming carton orders are typically < 2000; above that is suspect
SELECT
    order_id,
    distributor_id,
    quantity,
    CASE
        WHEN quantity IS NULL          THEN 'Missing'
        WHEN quantity > 2000           THEN 'Suspicious — possible pack-level entry'
        WHEN quantity < 1              THEN 'Invalid — less than 1'
        ELSE 'OK'
    END AS quantity_flag
FROM orders
ORDER BY quantity_flag, quantity DESC;

-- 2b. Explicit CAST example — convert quantity to INTEGER for reporting
--     (safe only after confirming no decimal values matter)
SELECT
    order_id,
    quantity                          AS original_qty,
    CAST(quantity AS INT)             AS qty_as_int,
    quantity::INT                     AS qty_alt_syntax   -- PostgreSQL shorthand
FROM orders
WHERE quantity IS NOT NULL;

-- 2c. Correcting a suspicious value (update with a comment for audit trail)
--     order_id 3 had 20000 — likely 200 cartons, not 20000 packs
UPDATE orders
SET quantity = 200,
    status   = status   -- placeholder; add a notes column in production
WHERE order_id = 3
  AND quantity = 20000;

-- Verify the correction
SELECT order_id, quantity FROM orders WHERE order_id = 3;


-- ============================================================
-- MODULE 3: JOINING TABLES
-- Abena's brief: "Pull all distributors AND their orders,
--                 including those with NO orders this quarter."
-- ============================================================

-- 3a. INNER JOIN — only distributors who have placed at least one order
SELECT
    d.distributor_id,
    d.distributor_name,
    d.region,
    COUNT(o.order_id)        AS order_count,
    SUM(o.quantity)          AS total_qty
FROM distributors d
INNER JOIN orders o ON d.distributor_id = o.distributor_id
GROUP BY d.distributor_id, d.distributor_name, d.region
ORDER BY total_qty DESC;

-- 3b. LEFT JOIN — all distributors, including those with zero orders (this quarter)
--     "This quarter" = Q4 2024 (Oct–Dec) based on the dataset
SELECT
    d.distributor_id,
    d.distributor_name,
    d.region,
    COUNT(o.order_id)        AS order_count,
    COALESCE(SUM(o.quantity), 0) AS total_qty
FROM distributors d
LEFT JOIN orders o
    ON d.distributor_id = o.distributor_id
    AND o.order_date BETWEEN '2024-10-01' AND '2024-12-31'
GROUP BY d.distributor_id, d.distributor_name, d.region
ORDER BY order_count, total_qty;



-- 3d. Validate joins — compare row counts before and after
--     Before: raw orders rows
SELECT COUNT(*) AS raw_orders FROM orders;

--     After INNER JOIN: should not exceed raw_orders
SELECT COUNT(*) AS joined_rows
FROM orders o
INNER JOIN distributors d ON o.distributor_id = d.distributor_id;


-- ============================================================
-- MODULE 4: CORE FUNCTIONS & LOGIC
-- Abena's brief: "Standardise distributor names — 'Tema Dist.', 
--                 'Tema Distributors', 'tema distributors' → one clean value."
-- ============================================================

-- 4b. String-clean preview (TRIM + UPPER for comparison; INITCAP for display)
SELECT
    distributor_id,
    distributor_name                              AS raw_name,
    TRIM(distributor_name)                        AS trimmed,
    UPPER(TRIM(distributor_name))                 AS uppercased,
    INITCAP(TRIM(distributor_name))               AS title_cased
FROM distributors;

-- 4d. Standardise region inconsistencies (Greater Accra / Accra / GA → 'Greater Accra')
UPDATE distributors
SET region = 'Greater Accra'
WHERE LOWER(TRIM(region)) IN ('accra', 'ga', 'greater accra');

-- Also fix the orders table region column
UPDATE orders
SET region = 'Greater Accra'
WHERE LOWER(TRIM(region)) IN ('accra', 'ga', 'greater accra');

-- 4e. CASE — flag inactive distributors (no orders this quarter)
WITH this_quarter_orders AS (
    SELECT DISTINCT distributor_id
    FROM orders
    WHERE order_date BETWEEN '2024-10-01' AND '2024-12-31'
)
SELECT
    d.distributor_id,
    d.distributor_name,
    d.region,
    CASE
        WHEN tq.distributor_id IS NOT NULL THEN 'Active'
        ELSE 'Inactive — follow up'
    END AS activity_flag
FROM distributors d
LEFT JOIN this_quarter_orders tq ON d.distributor_id = tq.distributor_id
ORDER BY activity_flag, d.distributor_name;

-- 4f. UNION ALL — combine order data from two hypothetical regional tables
--     (Illustrative: in practice these would be separate region tables)
SELECT 'Northern Region' AS source, order_id, quantity, order_date
FROM orders WHERE region = 'Northern'
UNION ALL
SELECT 'Volta Region',             order_id, quantity, order_date
FROM orders WHERE region = 'Volta'
ORDER BY order_date;


-- ============================================================
-- MODULE 5: AGGREGATING & SUMMARISING DATA
-- Abena's brief: "Which variants are moving fastest per region, by month?"
-- ============================================================

-- 5a. Total quantity sold per variant per region per month
SELECT
    o.region,
    pv.variant_name,
    TO_CHAR(o.order_date, 'YYYY-MM')  AS order_month,
    SUM(o.quantity)                   AS total_qty_sold,
    COUNT(o.order_id)                 AS order_count
FROM orders o
JOIN product_variants pv ON o.variant_id = pv.variant_id
WHERE o.quantity IS NOT NULL
GROUP BY o.region, pv.variant_name, TO_CHAR(o.order_date, 'YYYY-MM')
ORDER BY o.region, order_month, total_qty_sold DESC;

-- 5b. Top variant per region (using DISTINCT ON — PostgreSQL-specific)
SELECT DISTINCT ON (region)
    region,
    variant_name,
    total_qty_sold
FROM (
    SELECT
        o.region,
        pv.variant_name,
        SUM(o.quantity) AS total_qty_sold
    FROM orders o
    JOIN product_variants pv ON o.variant_id = pv.variant_id
    WHERE o.quantity IS NOT NULL
    GROUP BY o.region, pv.variant_name
) ranked
ORDER BY region, total_qty_sold DESC;

-- 5c. HAVING — only show region-variant combos with >200 units sold
SELECT
    o.region,
    pv.variant_name,
    SUM(o.quantity) AS total_qty_sold
FROM orders o
JOIN product_variants pv ON o.variant_id = pv.variant_id
WHERE o.quantity IS NOT NULL
GROUP BY o.region, pv.variant_name
HAVING SUM(o.quantity) > 200
ORDER BY total_qty_sold DESC;

-- 5d. COUNT(*) vs COUNT(column) — illustrating null handling
SELECT
    COUNT(*)         AS total_rows,          -- counts every row incl. nulls
    COUNT(quantity)  AS rows_with_quantity,  -- excludes nulls
    COUNT(DISTINCT variant_id) AS distinct_variants
FROM orders;


-- ============================================================
-- MODULE 6: CATEGORICAL DATA, TEXT & DATES
-- Abena's brief: "Pull back-to-school orders (September), 
--                 segment distributors by recency, flag public holidays."
-- ============================================================

-- 6a. Orders from the back-to-school period (September 2024)
SELECT
    o.order_id,
    d.distributor_name,
    pv.variant_name,
    o.quantity,
    o.order_date,
    o.region
FROM orders o
JOIN distributors d    ON o.distributor_id = d.distributor_id
JOIN product_variants pv ON o.variant_id   = pv.variant_id
WHERE EXTRACT(YEAR  FROM o.order_date) = 2024
  AND EXTRACT(MONTH FROM o.order_date) = 9
ORDER BY o.order_date;

-- 6b. Date arithmetic — days since last order per distributor
SELECT
    d.distributor_id,
    d.distributor_name,
    MAX(o.order_date)                         AS last_order_date,
    CURRENT_DATE - MAX(o.order_date)          AS days_since_last_order
FROM distributors d
LEFT JOIN orders o ON d.distributor_id = o.distributor_id
GROUP BY d.distributor_id, d.distributor_name
ORDER BY days_since_last_order DESC NULLS LAST;

-- 6c. Recency segmentation using CASE
WITH recency AS (
    SELECT
        d.distributor_id,
        d.distributor_name,
        MAX(o.order_date) AS last_order_date,
        CURRENT_DATE - MAX(o.order_date) AS days_since
    FROM distributors d
    LEFT JOIN orders o ON d.distributor_id = o.distributor_id
    GROUP BY d.distributor_id, d.distributor_name
)
SELECT
    distributor_id,
    distributor_name,
    last_order_date,
    days_since,
    CASE
        WHEN last_order_date IS NULL  THEN 'Never ordered'
        WHEN days_since <= 30         THEN 'Active (≤30 days)'
        WHEN days_since <= 90         THEN 'At risk (31–90 days)'
        ELSE 'Lapsed (>90 days)'
    END AS recency_segment
FROM recency
ORDER BY days_since DESC NULLS LAST;


-- 6e. Extracting date parts and DATE_TRUNC for time-based grouping
SELECT
    EXTRACT(YEAR  FROM order_date)             AS yr,
    EXTRACT(MONTH FROM order_date)             AS mth,
    EXTRACT(DOW   FROM order_date)             AS day_of_week, -- 0=Sun
    DATE_TRUNC('month', order_date)::DATE      AS month_start,
    COUNT(*)                                   AS orders_in_period
FROM orders
GROUP BY yr, mth, day_of_week, month_start
ORDER BY month_start;


-- ============================================================
-- MODULE 7: THE CEO REPORT — FULL END-TO-END PIPELINE
-- Abena's brief: "Top distributors, best regions, lagging variants — 
--                 clean summary table before the all-hands meeting."
-- ============================================================

WITH

-- STEP 1: Profile — flag and exclude bad rows
cleaned_orders AS (
    SELECT
        order_id,
        distributor_id,
        variant_id,
        quantity,
        order_date,
        -- Standardise region at query time (belt-and-braces after UPDATE above)
        CASE
            WHEN LOWER(TRIM(region)) IN ('accra','ga','greater accra') THEN 'Greater Accra'
            ELSE INITCAP(TRIM(region))
        END AS region,
        status
    FROM orders
    WHERE quantity IS NOT NULL
      AND quantity BETWEEN 1 AND 2000   -- exclude suspicious values
      AND status <> 'Cancelled'
),

-- STEP 2: Standardise distributor names
cleaned_distributors AS (
    SELECT
        distributor_id,
        CASE
            WHEN LOWER(TRIM(distributor_name)) IN ('tema dist.','tema distributors')
            THEN 'Tema Distributors'
            ELSE INITCAP(TRIM(distributor_name))
        END AS distributor_name,
        CASE
            WHEN LOWER(TRIM(region)) IN ('accra','ga','greater accra') THEN 'Greater Accra'
            ELSE INITCAP(TRIM(region))
        END AS region
    FROM distributors
),

-- STEP 3: Join orders to distributors and product variants
enriched AS (
    SELECT
        co.order_id,
        cd.distributor_name,
        cd.region,
        pv.variant_name,
        co.quantity,
        co.quantity * pv.unit_price          AS revenue,
        co.order_date,
        co.status
    FROM cleaned_orders co
    JOIN cleaned_distributors cd ON co.distributor_id = cd.distributor_id
    JOIN product_variants pv     ON co.variant_id     = pv.variant_id
),

-- STEP 4a: Top distributors by revenue
top_distributors AS (
    SELECT
        distributor_name,
        region,
        COUNT(order_id)          AS total_orders,
        SUM(quantity)            AS total_units,
        ROUND(SUM(revenue), 2)   AS total_revenue
    FROM enriched
    GROUP BY distributor_name, region
),

-- STEP 4b: Region performance
region_performance AS (
    SELECT
        region,
        SUM(quantity)            AS region_units,
        ROUND(SUM(revenue), 2)   AS region_revenue,
        COUNT(DISTINCT distributor_name) AS active_distributors
    FROM enriched
    GROUP BY region
),

-- STEP 4c: Variant performance — flag lagging variants
variant_performance AS (
    SELECT
        variant_name,
        SUM(quantity)            AS total_units_sold,
        ROUND(SUM(revenue), 2)   AS total_revenue,
        CASE
            WHEN SUM(quantity) < 200 THEN 'Lagging ⚠️'
            WHEN SUM(quantity) < 500 THEN 'Average'
            ELSE 'Fast-moving ✅'
        END AS performance_tag
    FROM enriched
    GROUP BY variant_name
)

-- ============================================================
-- FINAL OUTPUT: CEO-READY SUMMARY
-- Run each SELECT below separately, or comment-out the others.
-- ============================================================

-- A) Top Distributors
SELECT 'Top Distributors' AS report_section, *
FROM top_distributors
ORDER BY total_revenue DESC;