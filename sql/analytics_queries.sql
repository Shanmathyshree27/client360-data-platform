-- 1. Ticket volume by priority

SELECT
    priority,
    COUNT(*) AS total_tickets
FROM fact_support_tickets
GROUP BY priority
ORDER BY total_tickets DESC;

-- 2. SLA compliance

SELECT
    slastatus,
    COUNT(*) AS total_tickets
FROM fact_support_tickets
GROUP BY slastatus
ORDER BY total_tickets DESC;

-- 3. Average resolution time by category

SELECT
    category,
    ROUND(AVG(resolutionhours)::numeric, 2)
        AS avg_resolution_hours
FROM fact_support_tickets
WHERE resolutionhours IS NOT NULL
GROUP BY category
ORDER BY avg_resolution_hours DESC;

SELECT
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE slastatus = 'Met'
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE slastatus IN ('Met', 'Breached')
            ),
            0
        ),
        2
    ) AS sla_compliance_percentage
FROM fact_support_tickets;

SELECT
    c.customername,
    c.industry,
    COUNT(t.ticketid) AS total_tickets
FROM fact_support_tickets t
JOIN dim_customers c
    ON t.customerkey = c.customerkey
GROUP BY
    c.customername,
    c.industry
ORDER BY total_tickets DESC
LIMIT 10;

SELECT
    a.agentname,
    a.team,
    COUNT(t.ticketid) AS tickets_handled,
    ROUND(
        AVG(t.resolutionhours), 2
    ) AS avg_resolution_hours,
    COUNT(*) FILTER (
        WHERE t.slastatus = 'Breached'
    ) AS sla_breaches
FROM fact_support_tickets t
JOIN dim_agents a
    ON t.agentkey = a.agentkey
GROUP BY
    a.agentname,
    a.team
ORDER BY tickets_handled DESC;

SELECT
    c.industry,
    ROUND(AVG(f.rating), 2)
        AS avg_customer_rating,
    COUNT(*) AS total_feedback
FROM fact_customer_feedback f
JOIN fact_support_tickets t
    ON f.ticketid = t.ticketid
JOIN dim_customers c
    ON t.customerkey = c.customerkey
GROUP BY c.industry
ORDER BY avg_customer_rating DESC;


