ALTER TABLE inventory RENAME COLUMN price TO green_number;
ALTER TABLE inventory ADD COLUMN status TEXT CHECK(status IN ('yes', 'no')) DEFAULT 'no';
ALTER TABLE loans ADD COLUMN signature TEXT;