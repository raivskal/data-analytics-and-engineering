{{ config(materialized='table') }}

with snapshot as (

    select * from {{ ref('snap_customers') }}

),

current_versions as (

    select *
    from snapshot
    where dbt_valid_to is null

),

order_stats as (

    select
        customer_id,
        count(*)                                                  as order_count,
        sum(case when is_realised then order_amount else 0 end)   as realised_revenue,
        min(order_date)                                           as first_order_date,
        max(order_date)                                           as last_order_date
    from {{ ref('fct_orders') }}
    group by customer_id

),

-- Every customer known to the CRM or appearing on an order. Orders can
-- reference a customer before the CDC topic emits them, so the dimension has
-- to cover both sides or referential tests will flicker.
all_customers as (

    select customer_id from current_versions
    union
    select customer_id from order_stats

)

select
    a.customer_id,
    c.full_name,
    c.email,
    c.country,
    c.segment,
    (c.customer_id is not null)       as is_known_customer,
    coalesce(o.order_count, 0)        as order_count,
    coalesce(o.realised_revenue, 0)   as realised_revenue,
    o.first_order_date,
    o.last_order_date,
    (coalesce(o.order_count, 0) >= 3) as is_repeat_customer
from all_customers a
left join current_versions c on c.customer_id = a.customer_id
left join order_stats o      on o.customer_id = a.customer_id
