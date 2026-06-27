with sales as (
    select * from {{ ref('stg_sales_data') }}
),

final as (
    select
        sale_id,
        sale_amount,
        sale_date
    from sales
)

select * from final
