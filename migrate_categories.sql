-- Migración de la versión anterior: products.category (texto) a categories.id.
-- Respaldar la base y ejecutar una sola vez antes de actualizar la aplicación.
USE farmacia_inkafarma;

CREATE TABLE IF NOT EXISTS categories (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO categories (name)
SELECT DISTINCT COALESCE(NULLIF(category, ''), 'General') FROM products;

ALTER TABLE products ADD COLUMN category_id INT NULL;

UPDATE products p
JOIN categories c ON c.name = COALESCE(NULLIF(p.category, ''), 'General')
SET p.category_id = c.id;

ALTER TABLE products
  MODIFY category_id INT NOT NULL,
  ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id),
  DROP COLUMN category;
