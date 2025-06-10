-- Bus Pricing Pipeline Database Initialization
-- Creates initial database structure with indexes and constraints

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better query performance
-- Routes table indexes
CREATE INDEX IF NOT EXISTS idx_routes_origin ON routes(origin);
CREATE INDEX IF NOT EXISTS idx_routes_destination ON routes(destination);
CREATE INDEX IF NOT EXISTS idx_routes_origin_destination ON routes(origin, destination);

-- Operators table indexes  
CREATE INDEX IF NOT EXISTS idx_operators_name ON operators(name);
CREATE INDEX IF NOT EXISTS idx_operators_active ON operators(is_active);

-- Schedules table indexes
CREATE INDEX IF NOT EXISTS idx_schedules_route_id ON schedules(route_id);
CREATE INDEX IF NOT EXISTS idx_schedules_operator_id ON schedules(operator_id);
CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(date);
CREATE INDEX IF NOT EXISTS idx_schedules_departure_time ON schedules(departure_time);
CREATE INDEX IF NOT EXISTS idx_schedules_route_date ON schedules(route_id, date);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active);

-- Seat occupancy table indexes
CREATE INDEX IF NOT EXISTS idx_seat_occupancy_schedule_id ON seat_occupancy(schedule_id);
CREATE INDEX IF NOT EXISTS idx_seat_occupancy_seat_type ON seat_occupancy(seat_type);
CREATE INDEX IF NOT EXISTS idx_seat_occupancy_timestamp ON seat_occupancy(timestamp);
CREATE INDEX IF NOT EXISTS idx_seat_occupancy_created_at ON seat_occupancy(created_at);
CREATE INDEX IF NOT EXISTS idx_seat_occupancy_schedule_seat_type ON seat_occupancy(schedule_id, seat_type);

-- Data quality log indexes
CREATE INDEX IF NOT EXISTS idx_data_quality_log_issue_type ON data_quality_log(issue_type);
CREATE INDEX IF NOT EXISTS idx_data_quality_log_timestamp ON data_quality_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_data_quality_log_record_id ON data_quality_log(record_id);

-- Pricing model results indexes
CREATE INDEX IF NOT EXISTS idx_pricing_results_schedule_id ON pricing_model_results(schedule_id);
CREATE INDEX IF NOT EXISTS idx_pricing_results_timestamp ON pricing_model_results(calculation_timestamp);

-- Add constraints for data integrity
-- Ensure fare is positive
ALTER TABLE seat_occupancy ADD CONSTRAINT chk_seat_occupancy_fare_positive 
    CHECK (fare > 0);

-- Ensure seat counts are non-negative
ALTER TABLE seat_occupancy ADD CONSTRAINT chk_seat_occupancy_seats_non_negative 
    CHECK (total_seats >= 0 AND occupied_seats >= 0);

-- Ensure occupancy rate is between 0 and 1
ALTER TABLE seat_occupancy ADD CONSTRAINT chk_seat_occupancy_rate_valid 
    CHECK (occupancy_rate >= 0 AND occupancy_rate <= 1);

-- Ensure distance is positive
ALTER TABLE routes ADD CONSTRAINT chk_routes_distance_positive 
    CHECK (distance_km > 0);

-- Ensure arrival is after departure
ALTER TABLE schedules ADD CONSTRAINT chk_schedules_arrival_after_departure 
    CHECK (arrival_time > departure_time);

-- Create a view for commonly used schedule + occupancy data
CREATE OR REPLACE VIEW schedule_occupancy_summary AS
SELECT 
    s.schedule_id,
    s.route_id,
    s.operator_id,
    s.departure_time,
    s.arrival_time,
    s.date,
    r.origin,
    r.destination,
    r.distance_km,
    o.name as operator_name,
    so.seat_type,
    so.total_seats,
    so.occupied_seats,
    so.occupancy_rate,
    so.fare,
    so.timestamp as occupancy_timestamp
FROM schedules s
JOIN routes r ON s.route_id = r.route_id
JOIN operators o ON s.operator_id = o.operator_id
LEFT JOIN seat_occupancy so ON s.schedule_id = so.schedule_id
WHERE s.is_active = true AND o.is_active = true;

-- Create a view for data quality metrics
CREATE OR REPLACE VIEW data_quality_metrics AS
SELECT 
    DATE(timestamp) as report_date,
    issue_type,
    COUNT(*) as issue_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE(timestamp)) as percentage_of_daily_issues
FROM data_quality_log
GROUP BY DATE(timestamp), issue_type
ORDER BY report_date DESC, issue_count DESC;

-- Create a function to calculate route popularity
CREATE OR REPLACE FUNCTION calculate_route_popularity(route_id_param INT, days_back INT DEFAULT 30)
RETURNS DECIMAL(5,3) AS $$
DECLARE
    avg_occupancy DECIMAL(5,3);
    record_count INT;
BEGIN
    -- Calculate average occupancy rate for the route over the specified period
    SELECT 
        COALESCE(AVG(occupancy_rate), 0),
        COUNT(*)
    INTO avg_occupancy, record_count
    FROM seat_occupancy so
    JOIN schedules s ON so.schedule_id = s.schedule_id
    WHERE s.route_id = route_id_param
      AND so.created_at >= CURRENT_DATE - INTERVAL '%s days' % days_back;
    
    -- Return popularity score (0.0 to 1.0)
    -- If no data, return neutral score of 0.5
    IF record_count = 0 THEN
        RETURN 0.5;
    END IF;
    
    RETURN LEAST(1.0, avg_occupancy);
END;
$$ LANGUAGE plpgsql;

-- Create a function to get route statistics
CREATE OR REPLACE FUNCTION get_route_statistics(route_id_param INT, days_back INT DEFAULT 7)
RETURNS TABLE(
    total_schedules BIGINT,
    avg_occupancy_rate DECIMAL(5,3),
    avg_fare DECIMAL(10,2),
    total_seats_available BIGINT,
    total_seats_occupied BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT s.schedule_id),
        COALESCE(AVG(so.occupancy_rate), 0)::DECIMAL(5,3),
        COALESCE(AVG(so.fare), 0)::DECIMAL(10,2),
        COALESCE(SUM(so.total_seats), 0),
        COALESCE(SUM(so.occupied_seats), 0)
    FROM schedules s
    LEFT JOIN seat_occupancy so ON s.schedule_id = so.schedule_id
    WHERE s.route_id = route_id_param
      AND s.date >= CURRENT_DATE - INTERVAL '%s days' % days_back
      AND s.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Insert sample metadata if tables are empty
INSERT INTO routes (route_id, origin, destination, distance_km) VALUES
(1, 'Mumbai', 'Pune', 148.0),
(2, 'Delhi', 'Agra', 206.0),
(3, 'Bangalore', 'Chennai', 346.0),
(4, 'Kolkata', 'Darjeeling', 595.0),
(5, 'Jaipur', 'Udaipur', 421.0),
(6, 'Hyderabad', 'Vijayawada', 275.0),
(7, 'Ahmedabad', 'Rajkot', 216.0),
(8, 'Kochi', 'Thiruvananthapuram', 205.0)
ON CONFLICT (route_id) DO NOTHING;

INSERT INTO operators (operator_id, name, contact_email, is_active) VALUES
(1, 'RedBus Express', 'contact@redbusexpress.com', true),
(2, 'VRL Travels', 'info@vrltravels.com', true),
(3, 'KSRTC', 'support@ksrtc.in', true),
(4, 'Orange Tours', 'bookings@orangetours.com', true),
(5, 'SRS Travels', 'help@srstravels.com', true),
(6, 'TSRTC', 'contact@tsrtc.telangana.gov.in', true)
ON CONFLICT (operator_id) DO NOTHING;

-- Create a trigger to automatically update occupancy_rate when seat data changes
CREATE OR REPLACE FUNCTION update_occupancy_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.total_seats > 0 THEN
        NEW.occupancy_rate := LEAST(1.0, NEW.occupied_seats::DECIMAL / NEW.total_seats);
    ELSE
        NEW.occupancy_rate := 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_occupancy_rate
    BEFORE INSERT OR UPDATE ON seat_occupancy
    FOR EACH ROW
    EXECUTE FUNCTION update_occupancy_rate();

-- Grant necessary permissions for the application user
-- Note: This assumes the application connects with the same user as specified in env vars
-- In production, you'd create a separate application user with limited permissions

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO PUBLIC;

-- Create an index for full-text search on route origins and destinations (future feature)
CREATE INDEX IF NOT EXISTS idx_routes_fulltext ON routes USING gin(to_tsvector('english', origin || ' ' || destination));

-- Performance tuning settings recommendations (commented out - would be set at database level)
-- These are recommendations for production deployment:
-- 
-- SET shared_buffers = '256MB';
-- SET effective_cache_size = '1GB';
-- SET maintenance_work_mem = '64MB';
-- SET checkpoint_completion_target = 0.9;
-- SET wal_buffers = '16MB';
-- SET default_statistics_target = 100;

-- Log completion
INSERT INTO data_quality_log (source_file, record_id, issue_type, issue_description, action_taken, timestamp)
VALUES ('init.sql', 'database_init', 'info', 'Database initialization completed successfully', 'initialized', CURRENT_TIMESTAMP); 