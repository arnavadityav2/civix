import duckdb
import os
import time

def aggregate_telecom_and_finance():
    print("==========================================================")
    print("DERIVED TELECOM & FINANCIAL GRAPH AGGREGATION")
    print("==========================================================")
    
    con = duckdb.connect(":memory:")
    
    # 1. Telecom Aggregation
    t0 = time.time()
    cdr_path = "demo_world_15k_output/cdrs/**/*.parquet"
    telecom_edges = con.execute(f"""
        SELECT 
            caller_person_id::TEXT AS src,
            callee_phone_id::TEXT AS dst,
            COUNT(*)::INT AS source_event_count,
            MIN(timestamp)::TEXT AS source_start_time,
            MAX(timestamp)::TEXT AS source_end_time
        FROM read_parquet('{cdr_path}')
        WHERE caller_person_id IS NOT NULL AND callee_phone_id IS NOT NULL
        GROUP BY caller_person_id, callee_phone_id
    """).fetchall()
    dur_telecom = time.time() - t0
    print(f"Aggregated {len(telecom_edges):,d} derived COMMUNICATED_WITH edges from 1.5M CDRs in {dur_telecom:.2f}s")

    # 2. Financial Aggregation
    t0 = time.time()
    txn_path = "demo_world_15k_output/transactions/**/*.parquet"
    financial_edges = con.execute(f"""
        SELECT 
            sender_account_id::TEXT AS src,
            receiver_account_id::TEXT AS dst,
            COUNT(*)::INT AS source_event_count,
            SUM(amount)::DOUBLE AS total_amount,
            MIN(timestamp)::TEXT AS first_seen,
            MAX(timestamp)::TEXT AS last_seen
        FROM read_parquet('{txn_path}')
        WHERE sender_account_id IS NOT NULL AND receiver_account_id IS NOT NULL
        GROUP BY sender_account_id, receiver_account_id
    """).fetchall()
    dur_fin = time.time() - t0
    print(f"Aggregated {len(financial_edges):,d} derived TRANSFERRED_FUNDS_TO edges from 309K transactions in {dur_fin:.2f}s")
    
    con.close()
    return len(telecom_edges), len(financial_edges)

if __name__ == "__main__":
    aggregate_telecom_and_finance()
