with source as (

    select * from {{ source('landing', 'customers') }}

),

cleaned as (

    select
        customer_id,
        email,
        full_name,
        country,
        segment,
        is_deleted,
        event_id,
        event_time,
        updated_at
    from source
    -- deleted customers stay in the snapshot history, but not in the active view
    where not is_deleted

)

select * from cleaned
