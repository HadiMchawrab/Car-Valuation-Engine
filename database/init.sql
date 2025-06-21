CREATE TABLE listings (
  id          SERIAL     PRIMARY KEY,
  site_        TEXT       NOT NULL,
  url_         TEXT       NOT NULL,
  title       TEXT       NOT NULL,
  price       NUMERIC    NOT NULL,
  currency    TEXT       NOT NULL,
  year_        INT        NOT NULL,
  make        TEXT       NOT NULL,
  model       TEXT       NOT NULL,
  loc         TEXT       NULL,
  created_at   TEXT  NOT NULL,
  image_urls  TEXT      NULL,
  UNIQUE KEY idx_url (url_(255))
);

-- Create indexes for faster querying
CREATE INDEX idx_make ON listings (make(255));
CREATE INDEX idx_model ON listings (model(255));
CREATE INDEX idx_year ON listings (year_);
CREATE INDEX idx_price ON listings (price);
CREATE INDEX idx_location ON listings (loc(255));

-- populate the table with sample data
INSERT INTO listings (site_, url_, title, price, currency, year_, make, model, loc, created_at, image_urls)
VALUES
  ('dubizzle.sa', 'http://dubizzle.sa/listing1', '2020 Toyota Camry SE - Excellent Condition', 75000, 'SAR', 2020, 'Toyota', 'Camry', 'Riyadh', '2025-06-15', 'http://example.com/image1.jpg,http://example.com/image2.jpg'),
  ('dubizzle.sa', 'http://dubizzle.sa/listing2', '2019 Honda Civic LX - Low Mileage', 65000, 'SAR', 2019, 'Honda', 'Civic', 'Jeddah', '2025-06-14', NULL),
  ('motory.sa', 'http://motory.sa/listing3', '2021 BMW X5 xDrive40i - Premium Package', 250000, 'SAR', 2021, 'BMW', 'X5', 'Dammam', '2025-06-10', 'http://example.com/bmw1.jpg'),
  ('motory.sa', 'http://motory.sa/listing4', '2022 Mercedes-Benz C300 - AMG Line', 220000, 'SAR', 2022, 'Mercedes-Benz', 'C300', 'Riyadh', '2025-06-12', 'http://example.com/merc1.jpg,http://example.com/merc2.jpg');