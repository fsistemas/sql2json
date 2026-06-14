CREATE TABLE IF NOT EXISTS sales (
    id    INT,
    month VARCHAR(20),
    amount DECIMAL(10, 2)
);

INSERT INTO sales (id, month, amount) VALUES
    (1, 'January',  5000.00),
    (2, 'February', 3200.50),
    (3, 'March',    7100.75);
