-- FAR 117 Complete Rule Set
-- Comprehensive Federal Aviation Regulation Part 117 rules for flight and duty time limitations

-- ============================================================================
-- FAR 117 FLIGHT AND DUTY TIME LIMITATIONS
-- ============================================================================

-- Clear existing FAR 117 data
DELETE FROM regulatory_rules WHERE category = 'far117';

-- Core duty time limits based on report time
INSERT INTO regulatory_rules (rule_id, category, section, title, description, rule_text, citation, authority, effective_date, is_hard_constraint, weight, applies_to, parameters) VALUES

-- Flight Duty Period Limits (117.13)
('FAR117_FDP_05_00_19_59', 'far117', '117.13(a)(1)', 'Flight Duty Period Limit - Report 0500-1959', 
'Maximum flight duty period of 14 hours for report times between 0500-1959 local time', 
'For flight duty periods that begin between 0500 and 1959 local time, the maximum flight duty period is 14 hours.',
'14 CFR 117.13(a)(1)', 'FAA', '2014-01-04', true, 1.00, 
'{"report_time_start": "05:00", "report_time_end": "19:59"}', 
'{"max_duty_hours": 14, "time_zone": "local"}'),

('FAR117_FDP_20_00_23_59', 'far117', '117.13(a)(2)', 'Flight Duty Period Limit - Report 2000-2359', 
'Maximum flight duty period of 12 hours for report times between 2000-2359 local time', 
'For flight duty periods that begin between 2000 and 2359 local time, the maximum flight duty period is 12 hours.',
'14 CFR 117.13(a)(2)', 'FAA', '2014-01-04', true, 1.00, 
'{"report_time_start": "20:00", "report_time_end": "23:59"}', 
'{"max_duty_hours": 12, "time_zone": "local"}'),

('FAR117_FDP_00_00_04_59', 'far117', '117.13(a)(3)', 'Flight Duty Period Limit - Report 0000-0459', 
'Maximum flight duty period of 10 hours for report times between 0000-0459 local time', 
'For flight duty periods that begin between 0000 and 0459 local time, the maximum flight duty period is 10 hours.',
'14 CFR 117.13(a)(3)', 'FAA', '2014-01-04', true, 1.00, 
'{"report_time_start": "00:00", "report_time_end": "04:59"}', 
'{"max_duty_hours": 10, "time_zone": "local"}'),

-- Flight Time Limits (117.11)
('FAR117_FLIGHT_TIME_2_PILOT', 'far117', '117.11(a)', 'Flight Time Limit - 2 Pilot Operations', 
'Maximum flight time of 8 hours in 24 consecutive hours for 2-pilot operations', 
'No certificate holder may schedule and no flightcrew member may accept an assignment for flight time during any 24 consecutive hours that exceeds 8 flight hours for 2-pilot operations.',
'14 CFR 117.11(a)', 'FAA', '2014-01-04', true, 1.00, 
'{"crew_composition": "2_pilot"}', 
'{"max_flight_hours_24h": 8}'),

('FAR117_FLIGHT_TIME_3_PILOT', 'far117', '117.11(b)', 'Flight Time Limit - 3 Pilot Operations', 
'Maximum flight time of 9 hours in 24 consecutive hours for 3-pilot operations with adequate rest facility', 
'No certificate holder may schedule and no flightcrew member may accept an assignment for flight time during any 24 consecutive hours that exceeds 9 flight hours for 3-pilot operations with adequate rest facility.',
'14 CFR 117.11(b)', 'FAA', '2014-01-04', true, 1.00, 
'{"crew_composition": "3_pilot", "rest_facility": "adequate"}', 
'{"max_flight_hours_24h": 9}'),

-- Rest Requirements (117.25)
('FAR117_MIN_REST_10H', 'far117', '117.25(a)', 'Minimum Rest Period - 10 Hours', 
'Minimum rest period of 10 hours between flight duty periods', 
'Before beginning any reserve or flight duty period, a flightcrew member must be given at least 10 consecutive hours of rest.',
'14 CFR 117.25(a)', 'FAA', '2014-01-04', true, 1.00, 
'{}', 
'{"min_rest_hours": 10, "consecutive": true}'),

('FAR117_MIN_REST_12H_TIME_ZONES', 'far117', '117.25(b)', 'Minimum Rest Period - Time Zone Changes', 
'Minimum rest period of 12 hours when crossing more than 60 degrees longitude', 
'If a flightcrew member crosses more than 60 degrees of longitude during a flight duty period, the minimum rest period is 12 hours.',
'14 CFR 117.25(b)', 'FAA', '2014-01-04', true, 1.00, 
'{"longitude_change": ">60"}', 
'{"min_rest_hours": 12, "consecutive": true}'),

-- Cumulative Limitations (117.23)
('FAR117_CUMULATIVE_100_28', 'far117', '117.23(a)', 'Cumulative Flight Time - 100 Hours in 28 Days', 
'No more than 100 flight hours in any 28 consecutive days', 
'No certificate holder may schedule and no flightcrew member may accept an assignment if the flightcrew member's total flight time will exceed 100 hours in any 28 consecutive days.',
'14 CFR 117.23(a)', 'FAA', '2014-01-04', true, 1.00, 
'{}', 
'{"max_flight_hours": 100, "period_days": 28}'),

('FAR117_CUMULATIVE_1000_365', 'far117', '117.23(b)', 'Cumulative Flight Time - 1000 Hours in 365 Days', 
'No more than 1000 flight hours in any 365 consecutive days', 
'No certificate holder may schedule and no flightcrew member may accept an assignment if the flightcrew member's total flight time will exceed 1000 hours in any 365 consecutive days.',
'14 CFR 117.23(b)', 'FAA', '2014-01-04', true, 1.00, 
'{}', 
'{"max_flight_hours": 1000, "period_days": 365}'),

-- Reserve Duty (117.21)
('FAR117_RESERVE_DUTY_14H', 'far117', '117.21(a)', 'Reserve Duty Limit - 14 Hours', 
'Reserve duty period may not exceed 14 hours', 
'Except as specified in paragraph (c) of this section, a reserve duty period may not exceed 14 hours.',
'14 CFR 117.21(a)', 'FAA', '2014-01-04', true, 1.00, 
'{"duty_type": "reserve"}', 
'{"max_duty_hours": 14}'),

-- Consecutive Nighttime Operations (117.17)
('FAR117_CONSECUTIVE_NIGHTS_3', 'far117', '117.17(a)', 'Consecutive Nighttime Operations Limit', 
'No more than 3 consecutive flight duty periods involving nighttime operations without 56 hours rest', 
'A flightcrew member may not be assigned to more than three consecutive flight duty periods that infringe on the window of circadian low without a rest period of at least 56 consecutive hours.',
'14 CFR 117.17(a)', 'FAA', '2014-01-04', true, 1.00, 
'{"operation_type": "nighttime"}', 
'{"max_consecutive_nights": 3, "required_rest_hours": 56}'),

-- Airport Standby (117.15)
('FAR117_AIRPORT_STANDBY_DUTY', 'far117', '117.15(a)', 'Airport Standby Duty Counting', 
'Airport standby time counts as duty time and may not exceed flight duty period limits', 
'Airport standby is defined as a defined duty period during which a flightcrew member is required by a certificate holder to be at an airport for a possible assignment.',
'14 CFR 117.15(a)', 'FAA', '2014-01-04', true, 1.00, 
'{"duty_type": "airport_standby"}', 
'{"counts_as": "duty_time"}'),

-- Split Duty (117.15)
('FAR117_SPLIT_DUTY_EXTENSION', 'far117', '117.15(c)', 'Split Duty Flight Duty Period Extension', 
'Flight duty period may be extended up to 2 hours with qualifying rest opportunity', 
'If a flightcrew member is provided with a rest opportunity (an opportunity to sleep) in a suitable accommodation, the time that the flightcrew member spends in the suitable accommodation is not part of that flightcrew member''s flight duty period if the rest opportunity is at least 3 hours.',
'14 CFR 117.15(c)', 'FAA', '2014-01-04', false, 0.8, 
'{"duty_type": "split"}', 
'{"max_extension_hours": 2, "min_rest_opportunity_hours": 3}'),

-- Deadhead Transportation (117.15)
('FAR117_DEADHEAD_TRANSPORTATION', 'far117', '117.15(e)', 'Deadhead Transportation Time', 
'Deadhead transportation is not considered a flight duty period but counts toward cumulative limits', 
'Deadhead transportation is not considered a flight duty period or a rest period. Time spent in deadhead transportation is not considered part of a rest period.',
'14 CFR 117.15(e)', 'FAA', '2014-01-04', false, 0.7, 
'{"transportation_type": "deadhead"}', 
'{"counts_toward_cumulative": true, "counts_as_fdp": false}'),

-- Augmented Operations (117.13)
('FAR117_AUGMENTED_CREW_3_PILOT', 'far117', '117.13(c)(1)', 'Augmented Crew - 3 Pilots', 
'Maximum flight duty period of 17 hours for 3-pilot augmented crew with adequate rest facility', 
'For flight duty periods with adequate rest facility and 3 pilots, the maximum flight duty period may be extended based on the number of flight segments.',
'14 CFR 117.13(c)(1)', 'FAA', '2014-01-04', false, 0.9, 
'{"crew_composition": "3_pilot_augmented", "rest_facility": "adequate"}', 
'{"max_duty_hours": 17, "segments_considered": true}'),

('FAR117_AUGMENTED_CREW_4_PILOT', 'far117', '117.13(c)(2)', 'Augmented Crew - 4 Pilots', 
'Maximum flight duty period of 18 hours for 4-pilot augmented crew with adequate rest facility', 
'For flight duty periods with adequate rest facility and 4 pilots, the maximum flight duty period may be extended based on the number of flight segments.',
'14 CFR 117.13(c)(2)', 'FAA', '2014-01-04', false, 0.9, 
'{"crew_composition": "4_pilot_augmented", "rest_facility": "adequate"}', 
'{"max_duty_hours": 18, "segments_considered": true}'),

-- Extensions (117.19)
('FAR117_UNFORESEEN_EXTENSION', 'far117', '117.19(a)', 'Unforeseen Operational Circumstances Extension', 
'Flight duty period may be extended beyond normal limits due to unforeseen circumstances', 
'The pilot in command and the certificate holder may extend flight duty periods and reduce rest periods to the extent necessary to safely complete the flight.',
'14 CFR 117.19(a)', 'FAA', '2014-01-04', false, 0.6, 
'{"circumstance": "unforeseen"}', 
'{"pic_approval_required": true, "safety_justification_required": true}'),

-- Training and Checking (117.1)
('FAR117_TRAINING_CHECKING_EXCLUSION', 'far117', '117.1(b)', 'Training and Checking Operations Exclusion', 
'Part 117 does not apply to training, checking, or ferry flights', 
'This part does not apply to any operation conducted by a certificate holder under part 91, 125, or 135 of this chapter if any segment is conducted as a domestic passenger, cargo, or mail operation.',
'14 CFR 117.1(b)', 'FAA', '2014-01-04', false, 0.5, 
'{"operation_type": ["training", "checking", "ferry"]}', 
'{"part_117_applies": false}'),

-- Fatigue Risk Management (117.5)
('FAR117_FATIGUE_EDUCATION', 'far117', '117.5', 'Fatigue Education and Awareness', 
'Certificate holders must provide fatigue education and awareness training', 
'Each certificate holder must provide each flightcrew member with education and awareness training on fatigue, the effects of fatigue on pilots, and fatigue countermeasures.',
'14 CFR 117.5', 'FAA', '2014-01-04', true, 0.8, 
'{}', 
'{"training_required": true, "annual_requirement": true}'),

-- Reporting and Recordkeeping (117.23)
('FAR117_RECORD_KEEPING', 'far117', '117.23(d)', 'Flight Time Record Keeping Requirements', 
'Certificate holders must maintain accurate records of flight time and duty periods', 
'Each certificate holder must maintain an individual record for each flightcrew member that includes the flightcrew member''s flight time and duty period.',
'14 CFR 117.23(d)', 'FAA', '2014-01-04', true, 0.9, 
'{}', 
'{"record_retention_months": 24, "individual_records_required": true}');

-- ============================================================================
-- FAR 117 TABLE A - MAXIMUM FLIGHT DUTY PERIOD
-- ============================================================================

-- This represents the complex table-based limits in 117.13
INSERT INTO regulatory_rules (rule_id, category, section, title, description, rule_text, citation, authority, effective_date, is_hard_constraint, weight, applies_to, parameters) VALUES

-- 2 Pilot Crew Limits
('FAR117_TABLE_A_2P_1SEG', 'far117', '117.13 Table A', 'Max FDP - 2 Pilot, 1 Segment', 
'Maximum flight duty period for 2-pilot crew with 1 flight segment varies by report time', 
'For 2-pilot operations with 1 flight segment, maximum FDP ranges from 9-14 hours depending on report time.',
'14 CFR 117.13 Table A', 'FAA', '2014-01-04', true, 1.00, 
'{"crew_size": 2, "segments": 1}', 
'{"fdp_limits": {"0500-0559": 14, "0600-0659": 14, "0700-1259": 14, "1300-1659": 13, "1700-2159": 12, "2200-0459": 9}}'),

('FAR117_TABLE_A_2P_2SEG', 'far117', '117.13 Table A', 'Max FDP - 2 Pilot, 2 Segments', 
'Maximum flight duty period for 2-pilot crew with 2 flight segments varies by report time', 
'For 2-pilot operations with 2 flight segments, maximum FDP ranges from 9-14 hours depending on report time.',
'14 CFR 117.13 Table A', 'FAA', '2014-01-04', true, 1.00, 
'{"crew_size": 2, "segments": 2}', 
'{"fdp_limits": {"0500-0559": 14, "0600-0659": 14, "0700-1259": 14, "1300-1659": 13, "1700-2159": 12, "2200-0459": 9}}'),

('FAR117_TABLE_A_2P_3PLUS_SEG', 'far117', '117.13 Table A', 'Max FDP - 2 Pilot, 3+ Segments', 
'Maximum flight duty period for 2-pilot crew with 3+ flight segments varies by report time', 
'For 2-pilot operations with 3 or more flight segments, maximum FDP is reduced by 30 minutes.',
'14 CFR 117.13 Table A', 'FAA', '2014-01-04', true, 1.00, 
'{"crew_size": 2, "segments": "3+"}', 
'{"fdp_reduction_minutes": 30}');

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================

-- Count of rules inserted
DO $$ 
DECLARE 
    rule_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO rule_count FROM regulatory_rules WHERE category = 'far117';
    RAISE NOTICE 'Inserted % FAR 117 rules into regulatory_rules table', rule_count;
END $$;