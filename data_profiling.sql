SELECT * FROM ecommerce_sales;

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT order_id) AS unique_orders
FROM ecommerce_sales;

SELECT
    `status_pesanan`,
    COUNT(*) AS total_orders
FROM ecommerce_sales
GROUP BY `status_pesanan`
ORDER BY total_orders DESC;

SELECT
    `alasan_pembatalan`,
    COUNT(*) AS total_orders
FROM ecommerce_sales
GROUP BY `alasan_pembatalan`
ORDER BY total_orders DESC;

SELECT
    product_categories,
    COUNT(*) AS total_rows,
    SUM(total_qty) AS total_quantity,
    SUM(total_returned_qty) AS returned_quantity,
    SUM(total_diskon) AS total_discount
FROM ecommerce_sales
GROUP BY product_categories
ORDER BY total_quantity DESC;

/*
Location
*/

SELECT
    CONCAT(kota_kabupaten, ', ', provinsi) AS wilayah,
    COUNT(DISTINCT order_id) AS jumlah_pesanan,
    SUM(total_pembayaran) AS profit
FROM ecommerce_sales
GROUP BY
    kota_kabupaten,
    provinsi
ORDER BY jumlah_pesanan DESC;

