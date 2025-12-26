# Temporal Operational Strategy & Maintenance Guide

This document outlines the strategic path from local development to a production-ready cloud deployment of Temporal, including critical maintenance procedures for data safety.

---

### 1. Local Development & Prototyping
**Strategy: Focus on Developer Velocity**

For quick prototyping, minimize infrastructure "noise" so you can focus on workflow logic.

*   **Recommended Command**: `./scripts/dev_control.sh start postgres`
*   **Persistent Data**: The database is now mounted to a named volume (`postgres_data`), ensuring your workflows survive a `docker-compose down`.

---

## 2. Cloud Deployment (Internal System)
**Strategy: Horizontal Scaling & Resource Isolation**

When moving to the cloud as an internal system, you need to transition from "all-in-one" to "separate roles."

*   **Recommended Config Pattern**: `docker-compose-multirole.yaml` (Logic only—convert these to Kubernetes/ECS/Nomad).
*   **Key Transitions**:
    *   **Separate Services**: Deploy `frontend`, `matching`, `history`, and `worker` as separate scaling groups.
    *   **Matching Service**: This is often the first bottleneck. Give it high CPU priority.
    *   **Internal Load Balancing**: Use a gRPC-aware load balancer (like NGINX in this repo or an AWS ALB with gRPC enabled) to distribute traffic across `frontend` instances.

---

## 3. Secure Cloud Deployment (mTLS)
**Strategy: Zero-Trust Communication**

For high-security environments, encryption in transit is mandatory.

*   **Recommended Command**: `./scripts/dev_control.sh start tls`
*   **mTLS Implementation**:
    *   **Internal mTLS**: Encrypt traffic *between* Temporal services (Frontend to History, etc.).
    *   **External mTLS**: Require certificates for any *Client* (your application) or *Worker* connecting to the Frontend.
*   **Secret Management**: Use a cloud-native secret manager (Vault, AWS Secrets Manager) to rotate the `.pem` certificates used by the containers.

---

## 4. Maintenance: Backup & Recovery
**Strategy: Multi-Layered Data Protection**

Temporal's data is split between **History** (Execution State) and **Visibility** (Search). You must back them up differently.

### A. Primary Data (Postgres/Cassandra)
The primary DB contains the "state of truth." If you lose this, you lose your workflows.
*   **Backup Method**: Use managed database backups (e.g., AWS RDS Snapshots) with Point-in-Time Recovery (PITR).
*   **Frequency**: Minimum daily snapshots + 5-minute transaction log backups.
*   **Safety**: Test your "Recovery Time Objective" (RTO) by performing a dry-run restoration once a month.

### B. Visibility Data (Elasticsearch/OpenSearch)
This is a secondary index.
*   **Efficient Backup**: Use Elasticsearch **Snapshot and Restore** to an S3/GCS bucket.
*   **Safety**: If you lose the Visibility data, you can actually **rebuild it** from the primary History DB using Temporal's `admin` tools, though this is slow for large datasets.

### 4. Management & Debugging Tools

Beyond the core server, there are several "UI" and management tools you can use:

### 1. Official Web UI (Included)
*   **Port**: `http://localhost:8080`
*   **Use Case**: The standard way to view running workflows, event history, and stack traces.

### 2. Management Scripts (Custom)
*   **`scripts/dev_control.sh`**: Start/Stop the dev environment with support for `postgres`, `tls`, or `all` modes.
*   **`scripts/dev_backup.sh [sql|zip]`**: Create logical backups of the Postgres or MySQL database. ZIP format is compressed for smaller storage.
*   **`scripts/dev_restore.sh [file]`**: Restore from a specific `.sql` or `.zip` backup. ZIP files are automatically extracted before restoration.
*   **`scripts/dev_manage-indices.sh`**: Manage Elasticsearch indices (only available in `all` or `tls` modes).

### 3. Temporal VS Code Extension

### C. The "Golden" Safety Net: Archival
For long-term compliance and safety, enable **Archival**.
*   **Function**: When a workflow closes, Temporal can move its entire history to cheap blob storage (S3/GCS).
*   **Recovery**: If your primary DB is corrupted beyond repair, these archives serve as an immutable record of everything that happened.

---

## 6. Serving Different Clients (Multi-Tenancy)
**Strategy: Isolation vs. Shared Infrastructure**

If you need one Temporal Cluster to serve different teams, projects, or end-customers, you have three layers of isolation:

### Layer 1: Namespaces (Strongest Isolation)
*   **What it is**: A logical partition within the cluster.
*   **Best For**: Different teams or large internal products.
*   **Benefits**: 
    *   **Isolation**: Workflows in Namespace A cannot see or signal workflows in Namespace B.
    *   **Custom Settings**: Each namespace can have its own **Retention Period** (e.g., Team A needs 30 days, Team B only needs 1 day).
    *   **Archival**: You can enable S3/GCS archival for specific namespaces and not others.

### Layer 2: Task Queues (Logical Separation)
*   **What it is**: A bucket where workers look for tasks.
*   **Best For**: Different microservices within the same project.
*   **Strategy**: Use a unique Task Queue name for each service (e.g., `client-auth-queue`, `order-processing-queue`). This ensures a bug in one client's worker doesn't impact the task processing of another.

### Layer 3: Custom Search Attributes (Soft Multi-Tenancy)
*   **What it is**: Tagging individual workflows with a "ClientID".
*   **Best For**: SaaS applications with thousands of external customers.
*   **Strategy**: Instead of creating 10,000 Namespaces (which creates overhead), use a single namespace and add a `ClientUUID` Search Attribute to every workflow. You can then filter all queries, dashboards, and billing logic by that ID.

---

## 7. Production Checklist
- [ ] **Resource Limits**: Set CPU/Memory limits on all containers to prevent one service (like Elasticsearch) from starving others.
- [ ] **Liveness/Readiness Probes**: Ensure your orchestrator knows when a service is actually ready to receive gRPC traffic.
- [ ] **Metrics Scrapying**: Ensure Prometheus is scraping all service ports (8000-8004).
- [ ] **Logging Driver**: Switch from local files to a centralized logger (Loki/CloudWatch/Datadog) so logs persist after a crash.
