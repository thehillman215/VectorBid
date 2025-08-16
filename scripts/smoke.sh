#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${PORT:-8050}}"
AUTH_HEADER=()  # used only for /export if VECTORBID_API_KEY is set
if [ -n "${VECTORBID_API_KEY:-}" ]; then
  AUTH_HEADER=(-H "x-api-key: ${VECTORBID_API_KEY}")
fi

say(){ printf "› %s\n" "$*"; }

fail(){ echo "✖ $1"; exit 1; }

say "Target: $BASE_URL"

say "health"
curl -fsS "$BASE_URL/health" | python -m json.tool >/dev/null || fail "/health failed"
echo "OK"

say "schemas"
curl -fsS "$BASE_URL/schemas" >/dev/null || fail "/schemas failed"
echo "OK"

read -r -d '' DATA <<'JSON' || true
{"pairings":[
  {"id":"P1","layover_city":"SAN","redeye":false,"rest_hours":12},
  {"id":"P2","layover_city":"SJU","redeye":false,"rest_hours":11},
  {"id":"P3","layover_city":"XXX","redeye":true,"rest_hours":9}
]}
JSON

read -r -d '' PREF <<'JSON' || true
{"pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO","equip":["73G"],
 "hard_constraints":{"no_red_eyes":true},
 "soft_prefs":{"layovers":{"prefer":["SAN","SJU"],"weight":1.0}}}
JSON

read -r -d '' CTX <<'JSON' || true
{"ctx_id":"ctx-u1","pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO",
 "equip":["73G"],"seniority_percentile":0.5,"commuting_profile":{},
 "default_weights":{"layovers":1.0}}
JSON

say "validate"
curl -fsS -X POST "$BASE_URL/validate" \
  -H "content-type: application/json" \
  -d "{\"preference_schema\":$PREF,\"context\":$CTX,\"pairings\":$DATA}" \
  >/dev/null || fail "/validate failed"
echo "OK"

# Build FeatureBundle for the rest
FB="{\"context\":$CTX,\"preference_schema\":$PREF,\"analytics_features\":{\"base_stats\":{\"SAN\":{\"award_rate\":0.65},\"SJU\":{\"award_rate\":0.55}}},\"compliance_flags\":{},\"pairing_features\":$DATA}"

say "optimize"
TOPK_JSON=$(curl -fsS -X POST "$BASE_URL/optimize" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"K\":5}") || fail "/optimize failed"
TOPK=$(python - "$TOPK_JSON" <<'PY'
import sys, json
print(json.dumps(json.loads(sys.argv[1])["candidates"]))
PY
) || fail "parse optimize response"
echo "OK"

say "strategy"
STRAT_JSON=$(curl -fsS -X POST "$BASE_URL/strategy" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"candidates\":$TOPK}") || fail "/strategy failed"
echo "OK"

say "generate_layers"
GEN_JSON=$(curl -fsS -X POST "$BASE_URL/generate_layers" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"candidates\":$TOPK}") || fail "/generate_layers failed"
ARTIFACT=$(python - "$GEN_JSON" <<'PY'
import sys, json
print(json.dumps(json.loads(sys.argv[1])["artifact"]))
PY
) || fail "parse generate_layers response"
echo "OK"

say "lint"
curl -fsS -X POST "$BASE_URL/lint" -H "content-type: application/json" \
  -d "{\"artifact\":$ARTIFACT}" >/dev/null || fail "/lint failed"
echo "OK"

say "export (api key header only if VECTORBID_API_KEY is set)"
EXP_JSON=$(curl -fsS -X POST "$BASE_URL/export" -H "content-type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d "{\"artifact\":$ARTIFACT}") || fail "/export failed"
python - "$EXP_JSON" <<'PY'
import sys, json, pathlib
p = json.loads(sys.argv[1])["export_path"]
print("Exported:", p)
exists = pathlib.Path(p).exists()
print("File exists:", exists)
if not exists:
    raise SystemExit(2)
PY
echo "OK"

echo "✓ smoke passed"
