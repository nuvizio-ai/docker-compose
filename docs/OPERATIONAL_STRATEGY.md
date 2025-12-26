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

---

## 8. Temporal Cron & Overlap Policies
**Strategy: Managing Backlog vs. Freshness**

If you use Temporal for Cron jobs, you must decide what happens when a new job is scheduled to start while the previous run is still failing or retrying. This is controlled by the **Overlap Policy**:

### 1. `SKIP` (Default)
*   **Behavior**: If the previous job is still running (or retrying), the new job is dropped.
*   **Best For**: Cleanups or synchronization tasks where "if I missed one, the next one will fix it."

### 2. `BUFFER_ONE`
*   **Behavior**: If the previous job is running, exactly **one** new job is queued. Once the current job finishes, that buffered job starts immediately. Any other jobs scheduled during that time are dropped.
*   **Best For**: Report generation where you want the latest data eventually, but don't want to run 5 identical reports.

### 3. `BUFFER_ALL`
*   **Behavior**: Every scheduled run is queued.
*   **Best For**: Critical data processing where every single execution is mandatory (e.g., billing cycles). 
*   **Warning**: This can lead to a "thundering herd" if several jobs queue up and then all start at once.

### 4. `CANCEL_OTHER`
*   **Behavior**: When a new job kicks in, it attempts to cancel the old running job.
*   **Best For**: Long-running simulations or calculations where only the results of the *latest* version matter.

---

---

## 9. Worker Scaling & Priority Management
**Strategy: How to "Allocate" more resources to High Priority**

Temporal does **not** have a native "Priority" field on tasks. You cannot send a task and mark it as `Priority: 10`. Instead, priority is handled through **Horizontal Scaling** and **Queue Isolation**.

### 1. The "Isolated Lane" Pattern
*   **Mechanism**: Put `critical_payment` on `critical-queue` and `background_log` on `default-queue`.
*   **Scaling**: Run 10 workers for the `critical-queue` and 1 worker for the `default-queue`. This "allocates" more CPU/Memory to the priority tasks.

### 2. Auto-Scaling (The "Auto Allocation")
Temporal exposes a metric called `temporal_task_queue_backlog`. In production (Kubernetes), you use a tool like **KEDA (Kubernetes Event-driven Autoscaling)**:
*   **Rule**: If `backlog` on `critical-queue` > 10, start more worker Pods instantly.
*   **Result**: The system "auto-allocates" resources exactly where the demand is.

### 3. Tuning Worker Capacity
Inside a single Python worker, you can control how many tasks it handles at once:
```python
worker = Worker(
    client,
    task_queue="my-queue",
    max_concurrent_activities=100, # Adjust based on CPU/RAM
    max_task_queue_activities_per_second=50, # Rate limiting
)
```

---

---

## 10. Real-time Suitability & Latency
**Strategy: When is Temporal "Too Slow"?**

Temporal is a **highly reliable** system, but it is not a **high-frequency/low-latency** system (like HFT or gaming engines). Because Temporal persists every event to the database to ensure reliability, there is unavoidable latency overhead.

### 1. The "Persistence Tax"
*   **Latency**: Every `execute_activity` or `start_workflow` call requires at least 2-3 round trips to the database (Postgres/Cassandra) and a context switch to a Worker.
*   **Typical Overhead**: Expect **20ms - 100ms** of overhead per step in your workflow.
*   **Soft Real-time**: Temporal is great for "Soft Real-time" (UI feedback, order processing, banking) where sub-second response is enough.
*   **Hard Real-time**: Temporal is **not suitable** for "Hard Real-time" (microsecond requirements, industrial control systems, or high-speed packet processing).

### 2. The Decision Matrix
| Use Case | Recommended? | Why? |
| :--- | :--- | :--- |
| **User Sign-up Flow** | ✅ Yes | Reliability is more important than 50ms of speed. |
| **Financial Transaction** | ✅ Yes | Correctness and state recovery are non-negotiable. |
| **Chat Messaging** | ⚠️ **Hybrid** | Use Direct (WebSockets) for **Display**, use Temporal for **Moderation, Archival, and Push Notifications**. |
| **Search Autocomplete** | ❌ No | Requires <10ms response; use a direct cache (Redis). |

---

## 11. Final Production Checklist
