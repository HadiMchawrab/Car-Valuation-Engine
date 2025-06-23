CREATE TABLE listings (
  id          SERIAL     PRIMARY KEY,
  website        TEXT       NOT NULL,
  web_url         TEXT       NOT NULL,
  title       TEXT       NOT NULL,
  kilometers  INT         NULL,
  price       NUMERIC    NOT NULL,
  currency    TEXT       NOT NULL,
  year_oM        INT        NOT NULL,
  make        TEXT       NOT NULL,
  model       TEXT       NOT NULL,
  loc         TEXT       NULL,
  created_at   TEXT  NOT NULL,
  image_urls  TEXT      NULL
);

-- Create indexes for faster querying
CREATE INDEX idx_make ON listings (make(255));
CREATE INDEX idx_model ON listings (model(255));
CREATE INDEX idx_year ON listings (year_oM);
CREATE INDEX idx_website ON listings (kilometers);
CREATE INDEX idx_price ON listings (price);
CREATE INDEX idx_location ON listings (loc(255));

-- populate the table with sample data
INSERT INTO listings (website,web_url, title, kilometers, price, currency, year_oM, make, model, loc, created_at, image_urls)
VALUES
  ('dubizzle.sa', 'http://dubizzle.sa/listing1', '2020 Toyota Camry SE - Excellent Condition', 56794, 75000, 'SAR', 2020, 'Toyota', 'Camry', 'Riyadh', '2025-06-15', 'https://images.dubizzle.com.lb/thumbnails/14393543-800x600.jpeg'),
  ('dubizzle.sa', 'http://dubizzle.sa/listing2', '2019 Honda Civic LX - Low Mileage', NULL, 65000, 'SAR', 2019, 'Honda', 'Civic', 'Jeddah', '2025-06-14', 'https://images.dubizzle.sa/thumbnails/2988719-800x600.jpeg'),
  ('motory.sa', 'http://motory.sa/listing3', '2021 BMW X5 xDrive40i - Premium Package', 345345, 250000, 'SAR', 2021, 'BMW', 'X5', 'Dammam', '2025-06-10', 'https://images.dubizzle.com.lb/thumbnails/13466800-800x600.jpeg'),
  ('motory.sa', 'http://motory.sa/listing4', '2022 Mercedes-Benz C300 - AMG Line', NULL, 220000, 'SAR', 2022, 'Mercedes-Benz', 'C300', 'Riyadh', '2025-06-12', 'https://images.dubizzle.sa/thumbnails/2514609-800x600.jpeg'),
  ('dubizzle.sa', 'http://duvizzle.sa/listing5', '2023 Ford F-150 Lariat - Fully Loaded', 123456, 180000, 'SAR', 2023, 'Ford', 'F-150', 'Khobar', '2025-06-11', 'https://images.dubizzle.sa/thumbnails/2502209-800x600.jpeg'),
  ('motory.sa', 'http://motory.sa/listing6', '2018 Nissan Altima SV - Great Value', NULL, 45000, 'SAR', 2018, 'Nissan', 'Altima', 'Medina', '2025-06-13', 'https://images.dubizzle.sa/thumbnails/2514600-800x600.jpeg'),
  ('dubizzle.sa', 'http://dubizzle.sa/listing7', '2020 Hyundai Elantra - Fuel Efficient', 78900, 55000, 'SAR', 2020, 'Hyundai', 'Elantra', 'Jeddah', '2025-06-16', 'https://images.dubizzle.com.lb/thumbnails/14318078-800x600.jpeg'),
  ('motory.sa', 'http://motory.sa/listing8', '2019 Kia Sportage - Family Friendly SUV', NULL, 70000, 'SAR', 2019, 'Kia', 'Sportage', 'Riyadh', '2025-06-17', 'https://images.dubizzle.sa/thumbnails/2502225-800x600.jpeg');