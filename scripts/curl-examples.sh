# export tokens first
# export PS_SHA_TOKEN=...
# Base URL
BASE="http://localhost:8000"

# Health
curl -s "$BASE/health"

# Hash
curl -s -X POST "$BASE/hash" \
  -H "Authorization: Bearer $PS_SHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payload":{"user":"alexa","action":"commit","ts":123},"breath":1,"meta":{"agent":"guardian"}}' | jq

# Verify
HASH_HEX="REPLACE"
SIG_HEX="REPLACE"
curl -s -X POST "$BASE/verify" \
  -H "Authorization: Bearer $PS_SHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"hash_hex\":\"$HASH_HEX\",\"signature_hex\":\"$SIG_HEX\"}" | jq

# Chat bind
curl -s -X POST "$BASE/chat-bind" \
  -H "Authorization: Bearer $PS_SHA_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: msg-0001" \
  -d '{"message":"Deploy guardian","context":{"repo":"blackboxprogramming/blackboxprogramming"},"breath":-1,"meta":{"topic":"deploy"}}' | jq
