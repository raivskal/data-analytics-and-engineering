{{ config(
    materialized='incremental',
    unique_key=['order_hour', 'currency'],
    incremental_strategy='delete+insert'
) }}

select
    order_hour,
    currency,
    count(*)                                                      as order_count,
    count(*) filter (where is_cancelled)                          as cancelled_orders,
    sum(order_amount)                                             as gross_revenue,
    sum(case when is_realised then order_amount else 0 end)       as realised_revenue
from {{ ref('fct_orders') }}

{% if is_incremental() %}
where order_hour >= (
        select coalesce(max(order_hour), timestamptz '1970-01-01')
        from {{ this }}
    ) - interval '{{ var("incremental_lookback_hours", 2) }} hours'
{% endif %}

group by order_hour, currency
