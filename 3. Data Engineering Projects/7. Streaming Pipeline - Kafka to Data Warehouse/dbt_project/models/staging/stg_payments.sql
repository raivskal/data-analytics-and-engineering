with source as (

    select * from {{ source('landing', 'payments') }}

),

renamed as (

    select
        payment_id,
        order_id,
        method,
        amount,
        status,
        event_id,
        event_time,
        updated_at,
        date_trunc('hour', event_time) as payment_hour,
        (status = 'captured')          as is_captured,
        (status = 'failed')            as is_failed
    from source

)

select * from renamed
