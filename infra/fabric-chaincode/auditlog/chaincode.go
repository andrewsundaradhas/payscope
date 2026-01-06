package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Ledger event schema:
// {
//   "event_id": "uuid",
//   "event_type": "INGEST | AGENT_DECISION | FORECAST",
//   "artifact_hash": "sha256",
//   "schema_version": "vX",
//   "timestamp": "UTC"
// }

type AuditLogContract struct {
	contractapi.Contract
}

type LedgerEvent struct {
	EventID      string `json:"event_id"`
	EventType    string `json:"event_type"`
	ArtifactHash string `json:"artifact_hash"`
	SchemaVer    string `json:"schema_version"`
	TimestampUTC string `json:"timestamp"`
}

type StoredEvent struct {
	Event       LedgerEvent `json:"event"`
	PayloadHash string      `json:"payload_hash_sha256"`
}

var (
	uuidRe  = regexp.MustCompile("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
	shaRe   = regexp.MustCompile("^[0-9a-f]{64}$")
	typeSet = map[string]bool{"INGEST": true, "AGENT_DECISION": true, "FORECAST": true}
)

func canonicalJSON(v any) ([]byte, error) {
	// Go's json.Marshal is stable for struct field order; for this schema, that's sufficient.
	// No additional whitespace.
	return json.Marshal(v)
}

func sha256Hex(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

func validateEvent(e *LedgerEvent) error {
	if !uuidRe.MatchString(e.EventID) {
		return fmt.Errorf("invalid event_id")
	}
	if !typeSet[e.EventType] {
		return fmt.Errorf("invalid event_type")
	}
	ah := e.ArtifactHash
	if len(ah) != 64 {
		return fmt.Errorf("artifact_hash must be 64 hex chars")
	}
	if !shaRe.MatchString(ah) {
		return fmt.Errorf("artifact_hash must be lowercase sha256 hex")
	}
	if e.SchemaVer == "" {
		return fmt.Errorf("schema_version required")
	}
	// Require RFC3339 timestamp; treat as UTC by normalization.
	_, err := time.Parse(time.RFC3339, e.TimestampUTC)
	if err != nil {
		return fmt.Errorf("timestamp must be RFC3339")
	}
	return nil
}

func (c *AuditLogContract) PutEvent(ctx contractapi.TransactionContextInterface, eventJSON string) (string, error) {
	var e LedgerEvent
	if err := json.Unmarshal([]byte(eventJSON), &e); err != nil {
		return "", fmt.Errorf("invalid json: %w", err)
	}
	if err := validateEvent(&e); err != nil {
		return "", err
	}

	key := "event:" + e.EventID
	existing, err := ctx.GetStub().GetState(key)
	if err != nil {
		return "", err
	}

	// Idempotency: same event_id must be identical payload.
	canon, err := canonicalJSON(e)
	if err != nil {
		return "", err
	}
	payloadHash := sha256Hex(canon)

	if existing != nil {
		var stored StoredEvent
		if err := json.Unmarshal(existing, &stored); err != nil {
			return "", fmt.Errorf("corrupt stored event")
		}
		if stored.PayloadHash != payloadHash {
			return "", errors.New("idempotency_violation: event_id exists with different payload")
		}
		// no-op
		return ctx.GetStub().GetTxID(), nil
	}

	stored := StoredEvent{Event: e, PayloadHash: payloadHash}
	out, err := json.Marshal(stored)
	if err != nil {
		return "", err
	}
	if err := ctx.GetStub().PutState(key, out); err != nil {
		return "", err
	}
	return ctx.GetStub().GetTxID(), nil
}

func (c *AuditLogContract) GetEvent(ctx contractapi.TransactionContextInterface, eventID string) (string, error) {
	if !uuidRe.MatchString(eventID) {
		return "", fmt.Errorf("invalid event_id")
	}
	key := "event:" + eventID
	b, err := ctx.GetStub().GetState(key)
	if err != nil {
		return "", err
	}
	if b == nil {
		return "", fmt.Errorf("not_found")
	}
	return string(b), nil
}

func main() {
	cc, err := contractapi.NewChaincode(&AuditLogContract{})
	if err != nil {
		panic(err)
	}
	if err := cc.Start(); err != nil {
		panic(err)
	}
}




