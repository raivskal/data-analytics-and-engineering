{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

with orders as (

    select * from {{ ref('stg_orders') }}

),

payments as (

    select * from {{ ref('stg_payments') }}

),

payment_rollup as (

    select
        order_id,
        sum(case when is_captured then amount else 0 end) as captured_amount,
        count(*)                                          as payment_count,
        max(event_time)                                   as last_payment_time
    from payments
    group by order_id

),

joined as (

    select
        o.order_id,
        o.customer_id,
        o.store_id,
        o.status,
        o.currency,
        o.order_amount,
        o.item_count,
        o.order_date,
        o.order_hour,
        o.event_time,
        o.updated_at,
        o.is_cancelled,
        o.is_realised,
        coalesce(p.captured_amount, 0) as captured_amount,
        coalesce(p.payment_count, 0)   as payment_count,
        p.last_payment_time
    from orders o
    left join payment_rollup p on p.order_id = o.order_id

)

select * from joined

{% if is_incremental() %}
-- Lookback window instead of a strict watermark: corrections that arrive a
-- couple of hours late still land in the next run, and the merge keeps it
-- idempotent. Widen via the `incremental_lookback_hours` var if needed.
where event_time >= (
        select coalesce(max(event_time), timestamptz '1970-01-01')
        from {{ this }}
    ) - interval '{{ var("incremental_lookback_hours", 2) }} hours'
   or last_payment_time >= (
        select coalesce(max(event_time), timestamptz '1970-01-01')
        from {{ this }}
    ) - interval '{{ var("incremental_lookback_hours", 2) }} hours'
{% endif %}
