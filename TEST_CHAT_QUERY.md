# Testing /chat/query Endpoint

## Prerequisites

1. Services running: `docker compose up -d`
2. JWT token available with `bank_id` claim
3. Data ingested (at least one bank with transactions)

## Test Command

### Basic Query

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the transaction volume?",
    "time_range": "30d"
  }'
```

### ANOMALY Intent

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why did fraud spike last week?",
    "time_range": "7d"
  }'
```

### COMPARE Intent

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare fraud rates across merchants",
    "time_range": "30d"
  }'
```

### FORECAST Intent

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Forecast transaction volume for next month",
    "time_range": "30d"
  }'
```

### WHAT_IF Intent

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What if fraud detection improves by 20%?",
    "time_range": "30d"
  }'
```

## Expected Response

```json
{
  "summary": "Human-readable summary based on query",
  "metrics": {
    "transaction_volume": 12345,
    "fraud_rate": 0.02,
    ...
  },
  "forecast": {
    "next_month_volume": 15000,
    ...
  },
  "confidence": 0.85,
  "intent": "ANOMALY",
  "agents_invoked": ["FraudAgent", "ComplianceAgent"]
}
```

## Error Cases

### Bank ID Mismatch

```bash
# JWT has bank_id=A, but X-Bank-Id=B
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_WITH_BANK_A>" \
  -H "X-Bank-Id: bank_uuid_B" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

**Expected:** 403 Forbidden with "bank_id_mismatch"

### Missing Headers

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

**Expected:** 401 Unauthorized or 400 Bad Request

## Validation Checklist

- [ ] Endpoint responds (200 OK)
- [ ] Intent classification works (all 5 intents)
- [ ] Bank isolation enforced (403 on mismatch)
- [ ] Structured response returned
- [ ] Agents invoked correctly per intent
- [ ] Metrics returned (if data exists)
- [ ] Confidence score present
- [ ] Logging includes intent, agents_invoked, bank_id



