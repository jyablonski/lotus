with sales as (
    select * from {{ ref('fct_sales') }}
),

final as (
    select
        sale_date,
        count(*) as total_sales_count,
        sum(sale_amount) as total_sales_amount
    from sales
    group by sale_date
)

select * from final
