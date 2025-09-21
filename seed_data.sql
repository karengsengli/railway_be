-- ================================
-- Seed Data for Bangkok and Osaka Train Systems
-- ================================

-- Bangkok Train Companies
INSERT INTO train_companies (name, code, status, region_id, website) VALUES
('Bangkok Mass Transit System', 'BTS', 'active', (SELECT id FROM regions WHERE name = 'Bangkok'), 'https://www.bts.co.th'),
('Mass Rapid Transit Authority', 'MRT', 'active', (SELECT id FROM regions WHERE name = 'Bangkok'), 'https://www.mrta.co.th');

-- Osaka Train Companies
INSERT INTO train_companies (name, code, status, region_id, website) VALUES
('JR West', 'JRW', 'active', (SELECT id FROM regions WHERE name = 'Osaka'), 'https://www.westjr.co.jp'),
('Nankai Electric Railway', 'NANKAI', 'active', (SELECT id FROM regions WHERE name = 'Osaka'), 'https://www.nankai.co.jp');

-- Bangkok Train Lines
INSERT INTO train_lines (company_id, name, code, color, status) VALUES
((SELECT id FROM train_companies WHERE code = 'BTS'), 'Sukhumvit Line', 'SUK', '#00A651', 'active'),
((SELECT id FROM train_companies WHERE code = 'BTS'), 'Silom Line', 'SIL', '#004B87', 'active'),
((SELECT id FROM train_companies WHERE code = 'MRT'), 'Blue Line', 'BLU', '#0066CC', 'active'),
((SELECT id FROM train_companies WHERE code = 'MRT'), 'Purple Line', 'PUR', '#663399', 'active');

-- Osaka Train Lines
INSERT INTO train_lines (company_id, name, code, color, status) VALUES
((SELECT id FROM train_companies WHERE code = 'JRW'), 'Osaka Loop Line', 'LOOP', '#F39800', 'active'),
((SELECT id FROM train_companies WHERE code = 'JRW'), 'JR Kansai Main Line', 'KANS', '#0072BC', 'active'),
((SELECT id FROM train_companies WHERE code = 'NANKAI'), 'Nankai Main Line', 'MAIN', '#1E90FF', 'active'),
((SELECT id FROM train_companies WHERE code = 'NANKAI'), 'Nankai Airport Line', 'ARPT', '#FF6347', 'active');

-- Bangkok BTS Sukhumvit Line Stations
INSERT INTO stations (line_id, name, code, lat, lng, station_order, status) VALUES
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Mo Chit', 'N8', 13.802418, 100.553318, 1, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Saphan Phut', 'N7', 13.800284, 100.547142, 2, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Senangkom', 'N6', 13.798150, 100.542966, 3, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Ari', 'N5', 13.795016, 100.537790, 4, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Sanam Pao', 'N4', 13.791882, 100.532614, 5, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Victory Monument', 'N3', 13.766284, 100.537342, 6, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Phaya Thai', 'N2', 13.758384, 100.541842, 7, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Ratchathewi', 'N1', 13.751484, 100.546342, 8, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Siam', 'CEN', 13.744584, 100.550842, 9, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Chit Lom', 'E1', 13.742784, 100.548842, 10, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Phloen Chit', 'E2', 13.740984, 100.546842, 11, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Nana', 'E3', 13.739184, 100.544842, 12, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Asok', 'E4', 13.737384, 100.542842, 13, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Phrom Phong', 'E5', 13.735584, 100.540842, 14, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Thong Lo', 'E6', 13.733784, 100.538842, 15, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Ekkamai', 'E7', 13.731984, 100.536842, 16, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Phra Khanong', 'E8', 13.730184, 100.534842, 17, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'On Nut', 'E9', 13.728384, 100.532842, 18, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Bang Chak', 'E10', 13.726584, 100.530842, 19, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Punnawithi', 'E11', 13.724784, 100.528842, 20, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Udom Suk', 'E12', 13.722984, 100.526842, 21, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Bang Na', 'E13', 13.721184, 100.524842, 22, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'), 'Bearing', 'E14', 13.719384, 100.522842, 23, 'active');

-- Bangkok BTS Silom Line Stations
INSERT INTO stations (line_id, name, code, lat, lng, station_order, status) VALUES
((SELECT id FROM train_lines WHERE code = 'SIL'), 'National Stadium', 'W1', 13.746584, 100.529342, 1, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Siam', 'CEN', 13.744584, 100.533842, 2, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Ratchadamri', 'S1', 13.742584, 100.538342, 3, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Sala Daeng', 'S2', 13.740584, 100.542842, 4, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Chong Nonsi', 'S3', 13.738584, 100.547342, 5, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Surasak', 'S4', 13.736584, 100.551842, 6, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Saphan Taksin', 'S6', 13.734584, 100.556342, 7, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Krung Thon Buri', 'S7', 13.732584, 100.560842, 8, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Wongwian Yai', 'S8', 13.730584, 100.565342, 9, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Pho Nimit', 'S9', 13.728584, 100.569842, 10, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Talad Phlu', 'S10', 13.726584, 100.574342, 11, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Wutthakat', 'S11', 13.724584, 100.578842, 12, 'active'),
((SELECT id FROM train_lines WHERE code = 'SIL'), 'Bang Wa', 'S12', 13.722584, 100.583342, 13, 'active');

-- Osaka Stations (sample)
INSERT INTO stations (line_id, name, code, lat, lng, station_order, status) VALUES
((SELECT id FROM train_lines WHERE code = 'LOOP'), 'Osaka', 'OSK', 34.702485, 135.495951, 1, 'active'),
((SELECT id FROM train_lines WHERE code = 'LOOP'), 'Imamiya', 'IMM', 34.657685, 135.498951, 2, 'active'),
((SELECT id FROM train_lines WHERE code = 'LOOP'), 'Shin-Imamiya', 'SIM', 34.647685, 135.503951, 3, 'active'),
((SELECT id FROM train_lines WHERE code = 'LOOP'), 'Tennoji', 'TEN', 34.645685, 135.506951, 4, 'active'),
((SELECT id FROM train_lines WHERE code = 'LOOP'), 'Teradacho', 'TER', 34.643685, 135.509951, 5, 'active'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'), 'Namba', 'NAM', 34.666018, 135.500688, 1, 'active'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'), 'Imamiya Ebisu', 'IME', 34.657018, 135.505688, 2, 'active'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'), 'Sumiyoshi Taisha', 'SUM', 34.617018, 135.495688, 3, 'active'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'), 'Kansai Airport', 'KIX', 34.427299, 135.244049, 4, 'active');

-- Sample Routes for Bangkok BTS Sukhumvit Line
INSERT INTO routes (line_id, from_station_id, to_station_id, transport_type, duration_minutes, station_count, status) VALUES
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'E4'),
 'train', 35, 12, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 'train', 25, 8, 'active'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 (SELECT id FROM stations WHERE code = 'E4'),
 'train', 10, 4, 'active');

-- Sample Fare Rules for Bangkok BTS
-- Mo Chit to Asok (12 stations)
INSERT INTO fare_rules (line_id, from_station_id, to_station_id, passenger_type_id, base_price, currency) VALUES
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'E4'),
 (SELECT id FROM passenger_types WHERE name = 'adult'), 44.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'E4'),
 (SELECT id FROM passenger_types WHERE name = 'child'), 22.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'E4'),
 (SELECT id FROM passenger_types WHERE name = 'senior'), 30.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'E4'),
 (SELECT id FROM passenger_types WHERE name = 'member'), 39.60, 'THB');

-- Mo Chit to Siam (8 stations)
INSERT INTO fare_rules (line_id, from_station_id, to_station_id, passenger_type_id, base_price, currency) VALUES
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 (SELECT id FROM passenger_types WHERE name = 'adult'), 34.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 (SELECT id FROM passenger_types WHERE name = 'child'), 17.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 (SELECT id FROM passenger_types WHERE name = 'senior'), 23.00, 'THB'),
((SELECT id FROM train_lines WHERE code = 'SUK'),
 (SELECT id FROM stations WHERE code = 'N8'),
 (SELECT id FROM stations WHERE code = 'CEN'),
 (SELECT id FROM passenger_types WHERE name = 'member'), 30.60, 'THB');

-- Sample Fare Rules for Osaka Nankai Line
INSERT INTO fare_rules (line_id, from_station_id, to_station_id, passenger_type_id, base_price, currency) VALUES
((SELECT id FROM train_lines WHERE code = 'NANKAI'),
 (SELECT id FROM stations WHERE code = 'NAM'),
 (SELECT id FROM stations WHERE code = 'KIX'),
 (SELECT id FROM passenger_types WHERE name = 'adult'), 930.00, 'JPY'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'),
 (SELECT id FROM stations WHERE code = 'NAM'),
 (SELECT id FROM stations WHERE code = 'KIX'),
 (SELECT id FROM passenger_types WHERE name = 'child'), 470.00, 'JPY'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'),
 (SELECT id FROM stations WHERE code = 'NAM'),
 (SELECT id FROM stations WHERE code = 'KIX'),
 (SELECT id FROM passenger_types WHERE name = 'senior'), 650.00, 'JPY'),
((SELECT id FROM train_lines WHERE code = 'NANKAI'),
 (SELECT id FROM stations WHERE code = 'NAM'),
 (SELECT id FROM stations WHERE code = 'KIX'),
 (SELECT id FROM passenger_types WHERE name = 'member'), 837.00, 'JPY');