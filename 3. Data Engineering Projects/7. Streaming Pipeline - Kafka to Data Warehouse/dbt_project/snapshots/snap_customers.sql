{% snapshot snap_customers %}

{#
    SCD2 history for customers, driven by the customer CDC topic.
    Timestamp strategy: dbt opens/closes rows by comparing updated_at.
#}
{{ config(
    target_schema='snapshots',
    unique_key='customer_id',
    strategy='timestamp',
    updated_at='updated_at',
    invalidate_hard_deletes=true
) }}

select
    customer_id,
    email,
    full_name,
    country,
    segment,
    is_deleted,
    updated_at
from {{ source('landing', 'customers') }}

{% endsnapshot %}
