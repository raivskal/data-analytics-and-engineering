with source as (

    select * from {{ source('landing', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        store_id,
        status,
        currency,
        order_amount,
        item_count,
        event_id,
        event_time,
        updated_at,
        ingested_at,

        -- derived attributes the marts consistently rely on
        cast(event_time as date)                    as order_date,
        date_trunc('hour', event_time)              as order_hour,
        (status = 'cancelled')                      as is_cancelled,
        (status in ('paid', 'shipped'))             as is_realised
    from source

)

select * from renamed
