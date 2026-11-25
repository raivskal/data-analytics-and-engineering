-- Fails (returns rows) if the fact table holds more than one row per order,
-- i.e. if the incremental merge ever stops being idempotent.
select
    order_id,
    count(*) as row_count
from {{ ref('fct_orders') }}
group by order_id
having count(*) > 1
