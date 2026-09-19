#!/usr/bin/env bash
# End-to-end happy path with curl against a running server.
#
#   bash examples/quickstart_curl.sh
#
# Requires: curl, python3 (for JSON parsing). Uses synthetic data only.

set -euo pipefail

BASE_URL="${OE_BASE_URL:-http://localhost:8000}"
USERNAME="${OE_ADMIN_USERNAME:-admin}"
PASSWORD="${OE_ADMIN_PASSWORD:-admin}"
API="${BASE_URL}/api/v1"

jq_get() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo "1. Health"
curl -s "${API}/health" | python3 -m json.tool

echo "2. Authenticate"
TOKEN=$(curl -s -X POST "${API}/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" \
  | jq_get "['access_token']")
AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")
echo "   token acquired"

echo "3. Create organization"
ORG_ID=$(curl -s -X POST "${API}/organizations" "${AUTH[@]}" \
  -d '{"name":"Example District","code":"example-district","org_type":"district"}' \
  | jq_get "['id']")
echo "   organization: ${ORG_ID}"

echo "4. Create school"
SCHOOL_ID=$(curl -s -X POST "${API}/organizations/${ORG_ID}/schools" "${AUTH[@]}" \
  -d "{\"organization_id\":\"${ORG_ID}\",\"name\":\"Example School\",\"code\":\"example-school\"}" \
  | jq_get "['id']")
echo "   school: ${SCHOOL_ID}"

echo "5. Create a student identity reference (no PII)"
IDENTITY_ID=$(curl -s -X POST "${API}/identities" "${AUTH[@]}" \
  -d "{\"school_id\":\"${SCHOOL_ID}\",\"code\":\"student-001\"}" \
  | jq_get "['id']")
echo "   identity: ${IDENTITY_ID}"

echo "6. Record a check-in event (idempotent)"
curl -s -X POST "${API}/events" "${AUTH[@]}" \
  -d "{\"school_id\":\"${SCHOOL_ID}\",\"student_identity_id\":\"${IDENTITY_ID}\",\"event_kind\":\"check_in\",\"idempotency_key\":\"demo-00000001\"}" \
  | python3 -m json.tool

echo "7. Issue a credential"
CRED_ID=$(curl -s -X POST "${API}/credentials" "${AUTH[@]}" \
  -d "{\"student_identity_id\":\"${IDENTITY_ID}\",\"issuer_organization_id\":\"${ORG_ID}\",\"credential_type\":\"student_id_card\",\"title\":\"Example Student ID\"}" \
  | jq_get "['id']")
echo "   credential: ${CRED_ID}"

echo "8. Verify the credential"
curl -s -X POST "${API}/credentials/${CRED_ID}/verify" "${AUTH[@]}" \
  -d "{\"credential_id\":\"${CRED_ID}\",\"issuer_code\":\"example-district\"}" \
  | python3 -m json.tool

echo "9. Roll up attendance"
curl -s -X POST "${API}/attendance/rollup?school_id=${SCHOOL_ID}&day=2026-01-15" \
  "${AUTH[@]}" | python3 -m json.tool

echo "Done."