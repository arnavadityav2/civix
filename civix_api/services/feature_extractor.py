from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any

async def extract_candidate_features(session: AsyncSession, candidate_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Extracts the 70 features required by the behavioral XGBoost model from the database.
    Since we only consider features where the candidate is the initiator (CALLER or SENDER),
    we use two main CTEs to gather communication and financial events.
    """
    if not candidate_ids:
        return {}

    # Note: We zero-fill `txn_type_diversity` as documented in Task 3 limitations.
    query = text("""
        WITH candidate_comms AS (
            SELECT 
                ep_caller.entity_id AS candidate_id,
                e.event_id,
                e.event_type,
                e.occurred_at,
                ep_callee.entity_id AS callee_id,
                ep_tower.entity_id AS tower_id,
                ST_X(l.geometry) AS lon,
                ST_Y(l.geometry) AS lat,
                l.entity_id
            FROM civix.event_participant ep_caller
            JOIN civix.event e ON e.event_id = ep_caller.event_id
            LEFT JOIN civix.event_participant ep_callee 
                ON ep_callee.event_id = e.event_id AND ep_callee.participant_role = 'CALLEE'
            LEFT JOIN civix.event_participant ep_tower 
                ON ep_tower.event_id = e.event_id AND ep_tower.participant_role = 'CELL_TOWER'
            LEFT JOIN civix.location l ON l.entity_id = ep_tower.entity_id
            WHERE ep_caller.entity_id = ANY(:candidate_ids)
              AND ep_caller.participant_role = 'CALLER'
              AND e.event_type IN ('CALL', 'MESSAGE', 'DEVICE_PING')
        ),
        per_contact AS (
            SELECT 
                candidate_id, 
                callee_id, 
                COUNT(*) AS cnt
            FROM candidate_comms
            GROUP BY candidate_id, callee_id
        ),
        contact_conc AS (
            SELECT 
                candidate_id, 
                MAX(cnt)::float / GREATEST(SUM(cnt), 1) AS contact_concentration
            FROM per_contact
            GROUP BY candidate_id
        ),
        comm_features AS (
            SELECT 
                c.candidate_id,
                COUNT(*) AS total_calls,
                COUNT(DISTINCT (lower(c.occurred_at) AT TIME ZONE 'UTC')::date) AS active_days,
                COUNT(DISTINCT c.callee_id) AS unique_contacts,
                COUNT(DISTINCT c.tower_id) AS unique_cell_sectors,
                COUNT(*) FILTER (WHERE c.event_type = 'CALL') AS voice_calls,
                COUNT(*) FILTER (WHERE c.event_type = 'MESSAGE') AS sms_count,
                COUNT(*) FILTER (WHERE c.event_type = 'DEVICE_PING') AS data_sessions,
                COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (upper(c.occurred_at) - lower(c.occurred_at)))), 0) AS median_duration_sec,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (upper(c.occurred_at) - lower(c.occurred_at))) < 10)::float / GREATEST(COUNT(*), 1) AS short_call_ratio,
                COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM lower(c.occurred_at) AT TIME ZONE 'UTC') IN (22, 23, 0, 1, 2, 3, 4, 5)) AS night_call_count,
                COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM lower(c.occurred_at) AT TIME ZONE 'UTC') IN (22, 23, 0, 1, 2, 3, 4, 5))::float / GREATEST(COUNT(*), 1) AS night_call_ratio,
                COUNT(*) FILTER (WHERE EXTRACT(ISODOW FROM lower(c.occurred_at) AT TIME ZONE 'UTC') IN (6, 7))::float / GREATEST(COUNT(*), 1) AS weekend_call_ratio,
                COUNT(*)::float / GREATEST(COUNT(DISTINCT (lower(c.occurred_at) AT TIME ZONE 'UTC')::date), 1) AS calls_per_active_day,
                COALESCE(MAX(cc.contact_concentration), 0) AS contact_concentration,
                COUNT(DISTINCT (lower(c.occurred_at) AT TIME ZONE 'UTC')::date) AS location_active_days,
                COALESCE(stddev(EXTRACT(EPOCH FROM (upper(c.occurred_at) - lower(c.occurred_at)))) / NULLIF(AVG(EXTRACT(EPOCH FROM (upper(c.occurred_at) - lower(c.occurred_at)))), 0), 0) AS call_duration_cv,
                ((MAX(upper(c.occurred_at)) AT TIME ZONE 'UTC')::date - (MIN(lower(c.occurred_at)) AT TIME ZONE 'UTC')::date) + 1 AS comm_span_days,
                COALESCE(stddev(c.lat), 0) AS lat_stddev,
                COALESCE(stddev(c.lon), 0) AS lon_stddev,
                -- Geographic spread: lack of ST_StdDev for points is a limitation, but we can compute approx degrees using lat/lon bounding box
                SQRT(POWER(MAX(c.lat) - MIN(c.lat), 2) + POWER(MAX(c.lon) - MIN(c.lon), 2)) AS geo_spread_degrees,
                -- SCHEMA GAP: Location table lacks a `region` field (it was aggregated from cell towers offline), and we cannot spatial join polygons.
                -- We explicitly zero-fill this rather than collapsing it with unique_sectors.
                0 AS unique_regions,
                0 AS cross_region_ratio
            FROM candidate_comms c
            LEFT JOIN contact_conc cc ON cc.candidate_id = c.candidate_id
            GROUP BY c.candidate_id
        ),
        candidate_txs AS (
            SELECT 
                ep_sender.entity_id AS candidate_id,
                e.event_id,
                e.occurred_at,
                ep_receiver.entity_id AS receiver_id,
                COALESCE(CAST(NULLIF(a.object_value, '') AS NUMERIC), 0) AS amount
            FROM civix.event_participant ep_sender
            JOIN civix.event e ON e.event_id = ep_sender.event_id
            LEFT JOIN civix.event_participant ep_receiver 
                ON ep_receiver.event_id = e.event_id AND ep_receiver.participant_role = 'RECEIVER'
            LEFT JOIN civix.provenance p 
                ON p.source_id = e.event_id AND p.source_type = 'EVENT' AND p.derived_type = 'ASSERTION'
            LEFT JOIN civix.assertion a 
                ON a.assertion_id = p.derived_id AND a.predicate = 'TRANSFERRED_TO'
            WHERE ep_sender.entity_id = ANY(:candidate_ids)
              AND ep_sender.participant_role = 'SENDER'
              AND e.event_type = 'TRANSACTION'
        ),
        tx_features AS (
            SELECT 
                candidate_id,
                COUNT(*) AS total_transactions,
                COUNT(DISTINCT (lower(occurred_at) AT TIME ZONE 'UTC')::date) AS active_txn_days,
                SUM(amount) AS total_sent_amount,
                AVG(amount) AS avg_txn_amount,
                COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY amount), 0) AS median_txn_amount,
                MAX(amount) AS max_txn_amount,
                MIN(amount) AS min_txn_amount,
                COALESCE(stddev(amount), 0) AS std_txn_amount,
                COUNT(*) FILTER (WHERE amount > 10000) AS high_value_txn_count,
                COUNT(*) FILTER (WHERE amount > 10000)::float / GREATEST(COUNT(*), 1) AS high_value_txn_ratio,
                COALESCE(stddev(amount) / NULLIF(AVG(amount), 0), 0) AS txn_amount_cv,
                COUNT(DISTINCT receiver_id) AS unique_receivers,
                ((MAX(upper(occurred_at)) AT TIME ZONE 'UTC')::date - (MIN(lower(occurred_at)) AT TIME ZONE 'UTC')::date) + 1 AS txn_span_days
            FROM candidate_txs
            GROUP BY candidate_id
        ),
        per_receiver AS (
            SELECT 
                candidate_id, 
                receiver_id, 
                SUM(amount) AS cp_amount
            FROM candidate_txs
            GROUP BY candidate_id, receiver_id
        ),
        amount_conc AS (
            SELECT 
                candidate_id, 
                MAX(cp_amount)::float / NULLIF(SUM(cp_amount), 0) AS amount_concentration
            FROM per_receiver
            GROUP BY candidate_id
        ),
        demographics AS (
            SELECT 
                p.entity_id AS candidate_id,
                MAX(CASE WHEN p.gender = 'MALE' THEN 1 ELSE 0 END) AS gender_MALE,
                MAX(CASE WHEN p.gender = 'OTHER' THEN 1 ELSE 0 END) AS gender_OTHER,
                -- Occupations via assertions
                MAX(CASE WHEN a_occ.object_value = 'Businessman' THEN 1 ELSE 0 END) AS occupation_Businessman,
                MAX(CASE WHEN a_occ.object_value = 'Carpenter' THEN 1 ELSE 0 END) AS occupation_Carpenter,
                MAX(CASE WHEN a_occ.object_value = 'Contractor' THEN 1 ELSE 0 END) AS occupation_Contractor,
                MAX(CASE WHEN a_occ.object_value = 'Doctor' THEN 1 ELSE 0 END) AS occupation_Doctor,
                MAX(CASE WHEN a_occ.object_value = 'Driver' THEN 1 ELSE 0 END) AS occupation_Driver,
                MAX(CASE WHEN a_occ.object_value = 'Electrician' THEN 1 ELSE 0 END) AS occupation_Electrician,
                MAX(CASE WHEN a_occ.object_value = 'Engineer' THEN 1 ELSE 0 END) AS occupation_Engineer,
                MAX(CASE WHEN a_occ.object_value = 'Farmer' THEN 1 ELSE 0 END) AS occupation_Farmer,
                MAX(CASE WHEN a_occ.object_value = 'Government Employee' THEN 1 ELSE 0 END) AS occupation_Government_Employee,
                MAX(CASE WHEN a_occ.object_value = 'Hawker' THEN 1 ELSE 0 END) AS occupation_Hawker,
                MAX(CASE WHEN a_occ.object_value = 'Housewife' THEN 1 ELSE 0 END) AS occupation_Housewife,
                MAX(CASE WHEN a_occ.object_value = 'Laborer' THEN 1 ELSE 0 END) AS occupation_Laborer,
                MAX(CASE WHEN a_occ.object_value = 'Mechanic' THEN 1 ELSE 0 END) AS occupation_Mechanic,
                MAX(CASE WHEN a_occ.object_value = 'Police Officer' THEN 1 ELSE 0 END) AS occupation_Police_Officer,
                MAX(CASE WHEN a_occ.object_value = 'Shopkeeper' THEN 1 ELSE 0 END) AS occupation_Shopkeeper,
                MAX(CASE WHEN a_occ.object_value = 'Student' THEN 1 ELSE 0 END) AS occupation_Student,
                MAX(CASE WHEN a_occ.object_value = 'Tailor' THEN 1 ELSE 0 END) AS occupation_Tailor,
                MAX(CASE WHEN a_occ.object_value = 'Teacher' THEN 1 ELSE 0 END) AS occupation_Teacher,
                MAX(CASE WHEN a_occ.object_value = 'Trader' THEN 1 ELSE 0 END) AS occupation_Trader,
                -- Home Regions via assertions
                MAX(CASE WHEN loc.location_name ILIKE '%alwar%' THEN 1 ELSE 0 END) AS home_region_alwar,
                MAX(CASE WHEN loc.location_name ILIKE '%bharatpur%' THEN 1 ELSE 0 END) AS home_region_bharatpur,
                MAX(CASE WHEN loc.location_name ILIKE '%bikaner%' THEN 1 ELSE 0 END) AS home_region_bikaner,
                MAX(CASE WHEN loc.location_name ILIKE '%jaipur%' THEN 1 ELSE 0 END) AS home_region_jaipur,
                MAX(CASE WHEN loc.location_name ILIKE '%jodhpur%' THEN 1 ELSE 0 END) AS home_region_jodhpur,
                MAX(CASE WHEN loc.location_name ILIKE '%kota%' THEN 1 ELSE 0 END) AS home_region_kota,
                MAX(CASE WHEN loc.location_name ILIKE '%pali%' THEN 1 ELSE 0 END) AS home_region_pali,
                MAX(CASE WHEN loc.location_name ILIKE '%sikar%' THEN 1 ELSE 0 END) AS home_region_sikar,
                MAX(CASE WHEN loc.location_name ILIKE '%udaipur%' THEN 1 ELSE 0 END) AS home_region_udaipur
            FROM civix.person p
            LEFT JOIN civix.assertion a_occ ON a_occ.subject_entity_id = p.entity_id AND a_occ.predicate = 'EMPLOYED_BY'
            LEFT JOIN civix.assertion a_res ON a_res.subject_entity_id = p.entity_id AND a_res.predicate = 'RESIDED_AT'
            LEFT JOIN civix.location loc ON loc.entity_id = a_res.object_location_id
            WHERE p.entity_id = ANY(:candidate_ids)
            GROUP BY p.entity_id
        )
        SELECT 
            c.candidate_id,
            COALESCE(cf.total_calls, 0) AS total_calls,
            COALESCE(cf.active_days, 0) AS active_days,
            COALESCE(cf.unique_contacts, 0) AS unique_contacts,
            COALESCE(cf.unique_cell_sectors, 0) AS unique_cell_sectors,
            COALESCE(cf.voice_calls, 0) AS voice_calls,
            COALESCE(cf.sms_count, 0) AS sms_count,
            COALESCE(cf.data_sessions, 0) AS data_sessions,
            COALESCE(cf.median_duration_sec, 0) AS median_duration_sec,
            COALESCE(cf.short_call_ratio, 0) AS short_call_ratio,
            COALESCE(cf.night_call_count, 0) AS night_call_count,
            COALESCE(cf.night_call_ratio, 0) AS night_call_ratio,
            COALESCE(cf.weekend_call_ratio, 0) AS weekend_call_ratio,
            COALESCE(cf.calls_per_active_day, 0) AS calls_per_active_day,
            COALESCE(cf.contact_concentration, 0) AS contact_concentration,
            COALESCE(tf.unique_receivers, 0) AS unique_counterparties,
            0 AS txn_type_diversity, -- Explicit zero-fill per Task 3 limitation
            COALESCE(tf.total_sent_amount, 0) AS total_sent_amount,
            COALESCE(tf.avg_txn_amount, 0) AS avg_txn_amount,
            COALESCE(tf.median_txn_amount, 0) AS median_txn_amount,
            COALESCE(tf.max_txn_amount, 0) AS max_txn_amount,
            COALESCE(tf.min_txn_amount, 0) AS min_txn_amount,
            COALESCE(tf.std_txn_amount, 0) AS std_txn_amount,
            COALESCE(tf.high_value_txn_count, 0) AS high_value_txn_count,
            COALESCE(tf.high_value_txn_ratio, 0) AS high_value_txn_ratio,
            COALESCE(ac.amount_concentration, 0) AS amount_concentration,
            COALESCE(cf.unique_cell_sectors, 0) AS unique_sectors,
            COALESCE(cf.unique_regions, 0) AS unique_regions,
            COALESCE(cf.geo_spread_degrees, 0) AS geo_spread_degrees,
            COALESCE(cf.lat_stddev, 0) AS lat_stddev,
            COALESCE(cf.lon_stddev, 0) AS lon_stddev,
            COALESCE(cf.location_active_days, 0) AS location_active_days,
            COALESCE(cf.cross_region_ratio, 0) AS cross_region_ratio,
            ABS(COALESCE(cf.active_days, 0) - COALESCE(tf.active_txn_days, 0)) AS active_day_delta,
            CASE WHEN COALESCE(tf.total_transactions, 0) > 0 THEN cf.total_calls::float / tf.total_transactions ELSE 0 END AS calls_per_txn,
            COALESCE(cf.call_duration_cv, 0) AS call_duration_cv,
            COALESCE(tf.txn_amount_cv, 0) AS txn_amount_cv,
            COALESCE(cf.comm_span_days, 0) AS comm_span_days,
            COALESCE(tf.txn_span_days, 0) AS txn_span_days,
            COALESCE(cf.contact_concentration, 0) * COALESCE(ac.amount_concentration, 0) AS dual_concentration,
            (COALESCE(cf.unique_contacts, 0) + COALESCE(tf.unique_receivers, 0)) AS total_network_size,
            COALESCE(d.gender_MALE, 0) AS "gender_MALE",
            COALESCE(d.gender_OTHER, 0) AS "gender_OTHER",
            COALESCE(d.occupation_Businessman, 0) AS "occupation_Businessman",
            COALESCE(d.occupation_Carpenter, 0) AS "occupation_Carpenter",
            COALESCE(d.occupation_Contractor, 0) AS "occupation_Contractor",
            COALESCE(d.occupation_Doctor, 0) AS "occupation_Doctor",
            COALESCE(d.occupation_Driver, 0) AS "occupation_Driver",
            COALESCE(d.occupation_Electrician, 0) AS "occupation_Electrician",
            COALESCE(d.occupation_Engineer, 0) AS "occupation_Engineer",
            COALESCE(d.occupation_Farmer, 0) AS "occupation_Farmer",
            COALESCE(d.occupation_Government_Employee, 0) AS "occupation_Government Employee",
            COALESCE(d.occupation_Hawker, 0) AS "occupation_Hawker",
            COALESCE(d.occupation_Housewife, 0) AS "occupation_Housewife",
            COALESCE(d.occupation_Laborer, 0) AS "occupation_Laborer",
            COALESCE(d.occupation_Mechanic, 0) AS "occupation_Mechanic",
            COALESCE(d.occupation_Police_Officer, 0) AS "occupation_Police Officer",
            COALESCE(d.occupation_Shopkeeper, 0) AS "occupation_Shopkeeper",
            COALESCE(d.occupation_Student, 0) AS "occupation_Student",
            COALESCE(d.occupation_Tailor, 0) AS "occupation_Tailor",
            COALESCE(d.occupation_Teacher, 0) AS "occupation_Teacher",
            COALESCE(d.occupation_Trader, 0) AS "occupation_Trader",
            COALESCE(d.home_region_alwar, 0) AS home_region_alwar,
            COALESCE(d.home_region_bharatpur, 0) AS home_region_bharatpur,
            COALESCE(d.home_region_bikaner, 0) AS home_region_bikaner,
            COALESCE(d.home_region_jaipur, 0) AS home_region_jaipur,
            COALESCE(d.home_region_jodhpur, 0) AS home_region_jodhpur,
            COALESCE(d.home_region_kota, 0) AS home_region_kota,
            COALESCE(d.home_region_pali, 0) AS home_region_pali,
            COALESCE(d.home_region_sikar, 0) AS home_region_sikar,
            COALESCE(d.home_region_udaipur, 0) AS home_region_udaipur
        FROM unnest(CAST(:candidate_ids AS UUID[])) AS c(candidate_id)
        LEFT JOIN comm_features cf ON cf.candidate_id = c.candidate_id
        LEFT JOIN tx_features tf ON tf.candidate_id = c.candidate_id
        LEFT JOIN amount_conc ac ON ac.candidate_id = c.candidate_id
        LEFT JOIN demographics d ON d.candidate_id = c.candidate_id
    """)
    
    result = await session.execute(query, {"candidate_ids": candidate_ids})
    
    features = {}
    for row in result.mappings():
        cid = str(row["candidate_id"])
        feat_dict = dict(row)
        del feat_dict["candidate_id"]
        features[cid] = feat_dict
        
    return features
