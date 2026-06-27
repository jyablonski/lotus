with source as (
    select *
    from {{ source('revenue', 'sales_data') }}

    {% if is_incremental() %}
        where date > coalesce((select max(sale_date) from {{ this }}), '1970-01-01'::date)
    {% endif %}
),

renamed as (
    select
        id as sale_id,
        total_sales as sale_amount,
        date as sale_date
    from source
)

select * from renamed
