DROP TABLE IF EXISTS benchmark_items;
CREATE TABLE benchmark_items (
    id SERIAL PRIMARY KEY,
    name TEXT,
    sku TEXT,
    description TEXT,
    price DECIMAL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Generate 10k rows with unique timestamps
INSERT INTO benchmark_items (name, sku, description, price, updated_at)
SELECT 
    'Item ' || generate_series,
    'SKU-' || generate_series,
    'Description for item ' || generate_series,
    (random() * 100)::decimal(10,2),
    NOW() + (generate_series * interval '1 millisecond')
FROM generate_series(1, 10000);