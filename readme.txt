python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install -r requirements.txt
python -m app.main inventory/sample.yaml



🧠 EKS Fleet Orchestrator Platform
Multi-Tenant Multi-Cluster Upgrade & GitOps Automation Framework
🎯 Problem Statement

Our organization operates:

✅ Multiple tenants

✅ Each tenant in separate AWS Account

✅ Each tenant having multiple EKS clusters

✅ Each cluster running different workloads

✅ Separate infra GitOps + App GitOps

✅ Need for:

Requirement	Challenge
Upgrade 100+ clusters	Cannot upgrade manually
Canary rollout	Avoid fleet-wide failure
Parallel upgrade	Reduce downtime
Different apps per cluster	Deployment control
Central monitoring	Multi-cluster visibility
Tenant isolation	Account separation
Cost-optimized lower env upgrade	In-place upgrade

So we built an EKS Fleet Orchestrator Platform.

🏗️ High Level Architecture
                           ┌────────────────────────────┐
                           │   Blueprint Config Repo    │
                           │ (Tenant YAML Definitions)  │
                           └──────────────┬─────────────┘
                                          │
                                          │
                                Jenkins Job A
                           (Fleet Upgrade Pipeline)
                                          │
                                          ▼
                           ┌────────────────────────────┐
                           │ Python Fleet Orchestrator  │
                           │                            │
                           │ - Canary rollout           │
                           │ - Wave upgrade             │
                           │ - State lock (DynamoDB)    │
                           │ - Failure rollback         │
                           │ - Parallel upgrade         │
                           └──────────────┬─────────────┘
                                          │
                     Trigger Jenkins Job B per cluster
                                          │
                                          ▼
                         Jenkins Job B (Terraform)
                  ┌─────────────────────────────────────┐
                  │                                     │
                  │ terraform init                     │
                  │ terraform plan/apply               │
                  │ cluster_version upgrade           │
                  │ nodegroup AMI upgrade             │
                  │ addon upgrade                     │
                  │ ArgoCD cluster registration       │
                  │                                   │
                  └──────────────┬────────────────────┘
                                 │
                                 ▼
                         ArgoCD GitOps Platform
                   ┌─────────────────────────────┐
                   │ ApplicationSet Controller   │
                   │                             │
                   │ Cluster Labels             │
                   │ Fleet Labels              │
                   │ Env Labels                │
                   └──────────────┬────────────┘
                                  │
                                  ▼
                         Applications Deployed

⚙️ Repository Separation
Repo	Responsibility
infra-modules	Terraform Modules (EKS/VPC/etc)
infra-live	Terraform execution
blueprint-config	Tenant YAML
fleet-orchestrator	Upgrade Automation
gitops-platform	ArgoCD Infra Apps
gitops-apps	Business Apps
📄 Tenant Blueprint (Single Source of Truth)

This YAML drives:

Infra Creation

Upgrade

Application Deployment

tenant: tenant-a
env: dev
region: ap-south-1

services:
  eks:
    enabled: true
    config:
      dev-cpu-1:
        fleet: cpu
        is_canary: true
        version: "1.29"
        vpc_name: shared

      dev-cpu-2:
        fleet: cpu
        version: "1.29"

      dev-gpu-1:
        fleet: gpu
        version: "1.29"

🚀 Upgrade Strategy Supported
Strategy	Usage
Blue-Green	Production
In-Place	Lower env
Canary	Fleet safety
Wave Rollout	Parallel execution
Rollback	Auto stop
🟢 Blue-Green Upgrade Flow
Current Cluster (Blue)
        │
        ▼
Create Green Cluster
        │
Upgrade Control Plane
        │
Upgrade Nodegroups
        │
Upgrade Addons
        │
Register Cluster in ArgoCD
        │
Sync Infra GitOps
        │
Sync App GitOps
        │
Switch Traffic (Route53/ALB)
        │
Destroy Blue

🟡 In-Place Upgrade Flow
Python Orchestrator
        │
Trigger Terraform Job
        │
Upgrade Control Plane
        │
Upgrade Nodegroups
        │
Upgrade Addons
        │
ArgoCD Sync
        │
Done

🧪 Fleet Upgrade Execution Logic

1️⃣ Group clusters by fleet
2️⃣ Pick Canary cluster
3️⃣ Upgrade Canary
4️⃣ Bake Time
5️⃣ Rollout in Waves
6️⃣ Parallel upgrade per wave
7️⃣ Failure stops rollout

🔐 State Management

We use DynamoDB:

Purpose
Lock cluster during upgrade
Track upgrade success
Avoid re-upgrade
Resume failed wave
📦 Application Deployment

We use:

✅ ArgoCD
✅ ApplicationSet
✅ Cluster Label Matching

Cluster is registered with labels:

fleet=cpu
env=dev
tenant=tenant-a
gpu=false


ApplicationSet:

matchExpressions:
  - key: fleet
    operator: In
    values:
      - cpu


Apps automatically deploy only to matching clusters.

📊 Centralized Monitoring Architecture

Each Cluster:

Prometheus

Grafana

Loki

Remote Write → Central Monitoring Cluster

Cluster Prometheus
        │
Remote Write
        ▼
Central Prometheus
        │
Grafana Global Dashboard


So from single dashboard:

Cluster Health

Pod Failures

Node Usage

Upgrade status

🧰 Fleet Orchestrator Use Cases

EKS Upgrade

ArgoCD bootstrap

Monitoring rollout

Security patch rollout

AMI rotation

Cluster autoscaler config

Istio rollout

Nodegroup resize

Disaster Recovery

Cluster decommission