"""
CIVIX Synthetic World V2: PyArrow Schemas
civix_generator/v2/parquet_writer.py

Defines all output Parquet schemas.
These schemas must remain compatible with civix_ml feature pipeline.
No latent trait fields may appear in any schema here.
"""
import pyarrow as pa

# ── Person entity schema ──────────────────────────────────────────────────────
PERSON_SCHEMA = pa.schema([
    pa.field("person_id",     pa.string()),
    pa.field("person_index",  pa.int32()),
    pa.field("first_name",    pa.string()),
    pa.field("last_name",     pa.string()),
    pa.field("gender",        pa.string()),
    pa.field("dob",           pa.string()),
    pa.field("age_approx",    pa.int32()),
    pa.field("state",         pa.string()),
    pa.field("occupation",    pa.string()),
    pa.field("home_region",   pa.int32()),
])

# ── CDR schema ────────────────────────────────────────────────────────────────
CDR_SCHEMA = pa.schema([
    pa.field("cdr_id",            pa.string()),
    pa.field("caller_phone_id",   pa.string()),
    pa.field("callee_phone_id",   pa.string()),
    pa.field("timestamp",         pa.string()),
    pa.field("year",              pa.int32()),
    pa.field("month",             pa.int32()),
    pa.field("duration_seconds",  pa.int32()),
    pa.field("call_type",         pa.string()),
    pa.field("cell_sector_id",    pa.string()),
    pa.field("caller_person_id",  pa.string()),
    pa.field("callee_person_id",  pa.string()),
])

# ── Transaction schema ────────────────────────────────────────────────────────
TRANSACTION_SCHEMA = pa.schema([
    pa.field("transaction_id",       pa.string()),
    pa.field("txn_index",            pa.int32()),
    pa.field("sender_account_id",    pa.string()),
    pa.field("receiver_account_id",  pa.string()),
    pa.field("amount",               pa.float64()),
    pa.field("currency",             pa.string()),
    pa.field("transaction_type",     pa.string()),
    pa.field("timestamp",            pa.string()),
    pa.field("year",                 pa.int32()),
    pa.field("month",                pa.int32()),
    pa.field("sender_person_id",     pa.string()),
    # financial_pattern is a diagnostic field only — not for ML features
    pa.field("financial_pattern",    pa.string()),
])

# ── Account schema ────────────────────────────────────────────────────────────
ACCOUNT_SCHEMA = pa.schema([
    pa.field("account_id",         pa.string()),
    pa.field("account_index",      pa.int32()),
    pa.field("bank",               pa.string()),
    pa.field("account_type",       pa.string()),
    pa.field("masked_number",      pa.string()),
    pa.field("primary_holder_id",  pa.string()),
    pa.field("joint_holder_id",    pa.string()),
])

# ── Device schema ─────────────────────────────────────────────────────────────
DEVICE_SCHEMA = pa.schema([
    pa.field("device_id",        pa.string()),
    pa.field("device_index",     pa.int32()),
    pa.field("device_type",      pa.string()),
    pa.field("brand",            pa.string()),
    pa.field("primary_owner_id", pa.string()),
])

# ── SIM schema ────────────────────────────────────────────────────────────────
SIM_SCHEMA = pa.schema([
    pa.field("sim_id",              pa.string()),
    pa.field("sim_index",           pa.int32()),
    pa.field("operator",            pa.string()),
    pa.field("primary_holder_id",   pa.string()),
    pa.field("activation_day",      pa.int32()),
    pa.field("deactivation_day",    pa.int32()),
    pa.field("is_active",           pa.bool_()),
])

# ── Phone schema ──────────────────────────────────────────────────────────────
PHONE_SCHEMA = pa.schema([
    pa.field("phone_id",          pa.string()),
    pa.field("phone_index",       pa.int32()),
    pa.field("number_masked",     pa.string()),
    pa.field("primary_holder_id", pa.string()),
])

# ── Location schema ───────────────────────────────────────────────────────────
LOCATION_SCHEMA = pa.schema([
    pa.field("location_id",                pa.string()),
    pa.field("location_type",             pa.string()),
    pa.field("latitude",                  pa.float64()),
    pa.field("longitude",                 pa.float64()),
    pa.field("uncertainty_radius_meters", pa.int32()),
    pa.field("region",                    pa.string()),
    pa.field("description",               pa.string()),
])

# ── Cell sector schema ────────────────────────────────────────────────────────
CELL_SCHEMA = pa.schema([
    pa.field("cell_id",                    pa.string()),
    pa.field("location_type",             pa.string()),
    pa.field("centroid_latitude",         pa.float64()),
    pa.field("centroid_longitude",        pa.float64()),
    pa.field("azimuth_degrees",           pa.int32()),
    pa.field("beamwidth_degrees",         pa.int32()),
    pa.field("uncertainty_radius_meters", pa.int32()),
    pa.field("region",                    pa.string()),
    pa.field("description",               pa.string()),
])

# ── Ground truth label schema ─────────────────────────────────────────────────
# MUST ONLY be written to ground_truth/ directory
LABEL_SCHEMA = pa.schema([
    pa.field("entity_id",           pa.string()),
    pa.field("entity_type",         pa.string()),
    pa.field("person_index",        pa.int32()),
    pa.field("scenario_class",      pa.string()),
    pa.field("scenario_family",     pa.string()),
    pa.field("scenario_category",   pa.string()),
    pa.field("difficulty",          pa.string()),
    pa.field("is_positive_label",   pa.bool_()),
    pa.field("is_false_positive",   pa.bool_()),
    pa.field("is_low_visibility",   pa.bool_()),
    pa.field("is_hard_negative",    pa.bool_()),
    pa.field("is_bridge_node",      pa.bool_()),
    pa.field("in_criminal_network", pa.bool_()),
    pa.field("risk_score_gt",       pa.float32()),
    pa.field("ground_truth_note",   pa.string()),
])

# ── Train/val/test split schema ───────────────────────────────────────────────
SPLIT_SCHEMA = pa.schema([
    pa.field("entity_id",        pa.string()),
    pa.field("person_index",     pa.int32()),
    pa.field("split",            pa.string()),
    pa.field("active_start_day", pa.int32()),
    pa.field("scenario_class",   pa.string()),
])

# ── Community catalog schema ──────────────────────────────────────────────────
COMMUNITY_SCHEMA = pa.schema([
    pa.field("community_id",   pa.int32()),
    pa.field("type",           pa.string()),
    pa.field("size",           pa.int32()),
    pa.field("region",         pa.int32()),
    pa.field("is_criminal",    pa.bool_()),
])
