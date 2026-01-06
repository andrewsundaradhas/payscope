// Phase 4.4 — Neo4j schema (constraints + indexes)
// Prevent duplicate nodes and edges via uniqueness constraints.

// Nodes
CREATE CONSTRAINT transaction_pk_unique IF NOT EXISTS
FOR (t:Transaction) REQUIRE t.transaction_pk IS UNIQUE;

CREATE CONSTRAINT merchant_pk_unique IF NOT EXISTS
FOR (m:Merchant) REQUIRE m.merchant_pk IS UNIQUE;

CREATE CONSTRAINT bank_pk_unique IF NOT EXISTS
FOR (b:Bank) REQUIRE b.bank_pk IS UNIQUE;

CREATE CONSTRAINT network_name_unique IF NOT EXISTS
FOR (n:Network) REQUIRE n.name IS UNIQUE;

// Relationship identity (edge de-dup)
// Use edge_id = "<transaction_pk>|<RELTYPE>|<stage>" for uniqueness.
CREATE CONSTRAINT edge_id_unique IF NOT EXISTS
FOR ()-[r]-() REQUIRE r.edge_id IS UNIQUE;

// Helpful indexes
CREATE INDEX transaction_id_index IF NOT EXISTS
FOR (t:Transaction) ON (t.transaction_id);




