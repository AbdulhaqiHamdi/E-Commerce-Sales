SELECT
    SUBSTRING_INDEX(alasan_pembatalan, '. Alasan: ', 1) AS Status,
    SUBSTRING_INDEX(alasan_pembatalan, '. Alasan: ', -1) AS Alasan
FROM ecommerce_sales;

ALTER TABLE ecommerce_sales
ADD COLUMN cancellation_status VARCHAR(255),
ADD COLUMN cancellation_reason VARCHAR(255);

ALTER TABLE ecommerce_sales
DROP COLUMN source_file;

UPDATE ecommerce_sales
SET status_pesanan = 'Pengembalian dapat Diajukan'
WHERE status_pesanan LIKE 'Pesanan diterima, namun Pembeli masih dapat mengajukan pengembalian%';

UPDATE ecommerce_sales
SET
    cancellation_status = CASE
        WHEN alasan_pembatalan LIKE '%. Alasan: %'
        THEN SUBSTRING_INDEX(alasan_pembatalan, '. Alasan: ', 1)
        ELSE alasan_pembatalan
    END,

    cancellation_reason = CASE
        WHEN alasan_pembatalan LIKE '%. Alasan: %'
        THEN SUBSTRING_INDEX(alasan_pembatalan, '. Alasan: ', -1)
        ELSE NULL
    END;