ALTER TABLE purchase_order_items
  ADD COLUMN received_quantity DECIMAL(18,2) NOT NULL DEFAULT 0.00;

UPDATE purchase_order_items poi
JOIN purchase_orders po ON po.id=poi.purchase_order_id
SET poi.received_quantity=poi.quantity
WHERE po.status='received'
  AND poi.received_quantity=0;