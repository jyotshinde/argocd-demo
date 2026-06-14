# Argo CD Sync Waves Tutorial | Step-by-Step Hands-On

## Video reference for this lecture is the following:

[![Watch the video](https://img.youtube.com/vi/SrgaMOuiqyY/maxresdefault.jpg)](https://www.youtube.com/watch?v=SrgaMOuiqyY&ab_channel=CloudWithVarJosh)

---
## ⭐ Support the Project  
If this **repository** helps you, give it a ⭐ to show your support and help others discover it! 

---

## Table of Contents

* [Introduction](#introduction)  
* [How Kubernetes resources are created](#how-kubernetes-resources-are-created)  
  * [Resources created via kubectl (client-driven model)](#resources-created-via-kubectl-client-driven-model)  
  * [Resources created using Argo CD (control-plane–driven model)](#resources-created-using-argo-cd-control-plane–driven-model)  
  * [Default sequencing by resource kind](#default-sequencing-by-resource-kind)  
  * [Sequencing by name (final tie-breaker)](#sequencing-by-name-final-tie-breaker)  
  * [Critical takeaway](#critical-takeaway)  
* [Why Sync Waves?](#why-sync-waves)  
  * [Explicit dependencies (Kubernetes-enforced)](#1-explicit-dependencies-kubernetes-enforced)  
  * [Implicit dependencies (intent-based-not-enforced)](#2-implicit-dependencies-intent-based-not-enforced)  
  * [Ordering challenges without Sync Waves](#ordering-challenges-without-sync-waves)  
* [What Sync Waves are and how they work](#what-sync-waves-are-and-how-they-work)  
* [How Argo CD determines the final resource order](#how-argo-cd-determines-the-final-resource-order)  
* [How Sync Waves influence ordering in practice](#how-sync-waves-influence-ordering-in-practice)  
* [Where hooks fit](#where-hooks-fit)  
* [Demo: Argo CD Sync Waves](#demo-argo-cd-sync-waves)  
  * [Demo prerequisites](#demo-prerequisites)  
  * [Step 1: Create the Argo CD Application](#step-1-create-the-argo-cd-application)  
  * [Step 2: Create the Git repository](#step-2-create-the-git-repository)  
  * [Step 3: Perform a manual sync](#step-3-perform-a-manual-sync)  
  * [Step 4: Access the application](#step-4-access-the-application)  
* [Key takeaway](#key-takeaway)  
* [Conclusion](#conclusion)  
* [References](#references)  

---

## Introduction

Kubernetes is an API-driven system that allows resources to be created independently and in any order. While this flexibility enables powerful automation, it also places the responsibility of **correct sequencing and intent enforcement** on the client interacting with the cluster.

Tools like `kubectl`, CI/CD pipelines, and custom platforms submit resources to the Kubernetes API server without any built-in understanding of application-level intent. Argo CD improves this model by acting as a **control-plane client**, evaluating the full desired state of an application and applying resources deterministically.

However, deterministic ordering alone does not guarantee correct application behavior. This document explains **why Sync Waves exist**, how they differ from default ordering, and how they allow operators to explicitly encode **deployment intent** in a GitOps workflow.

---

## How Kubernetes resources are created

![Alt text](/images/7a.png)

Before understanding why features like Sync Waves exist, it is important to understand **how Kubernetes resources are created and applied**.
There are **two fundamentally different execution models**, depending on whether Argo CD is used or not.
In both cases, the Kubernetes API server is the final entry point, but the level of orchestration and intent awareness is very different.

---

**1. Resources created via kubectl (client-driven model)**

* **Manifests are submitted directly to the Kubernetes API server by kubectl, in file or document order, with no awareness of application structure, dependencies, or runtime readiness.**
  When you use `kubectl apply`, the kubectl client sends each manifest as an independent API request. kubectl does not understand that a Namespace, ConfigMap, ServiceAccount, Deployment, and Service together form a single application. The Kubernetes API server simply validates and persists each object it receives; it does not infer relationships or enforce ordering across resources.

* **Each object is persisted independently, with no orchestration or sequencing guarantees across resources.**
  From `kubectl`’s perspective, a resource is “done” once the API server accepts it. There is no built-in mechanism to ensure prerequisites exist before dependent resources are created.
  *Example:* A Deployment may be created before its ServiceAccount, Secret, or ConfigMap exist, even though the workload logically depends on them.


> **Note on Kubernetes clients and ordering**
> `kubectl` is just one of many clients. Kubernetes is fundamentally an **API-driven system**, and any authorized tool capable of making REST calls can interact with the cluster. Whether you use `kubectl`, Jenkins (invoking `kubectl`), Argo CD, client libraries (Go, Python, etc.), or custom platforms, **every interaction ultimately becomes a REST request to the kube-apiserver**.
>
> What differs is **who decides the order of those requests**. Resource creation and modification are not always driven by `kubectl`; CI pipelines, automation scripts, internal platforms, and tools like Argo CD can interact with the API server directly. In all client-driven models, the **client is responsible for deciding when and in what sequence** manifests are sent to the API server. Argo CD can be viewed as a specialized, opinionated control-plane client that adds built-in ordering and orchestration logic on top of these API interactions.


---

**2. Resources created using Argo CD (control-plane–driven model)**

* **Argo CD acts as a control plane, first evaluating all manifests belonging to an Application and computing a deterministic execution plan before interacting with the API server.**
  Argo CD loads every manifest associated with an Application and treats them as a single desired state defined in Git. It understands that a Namespace, ConfigMap, Deployment, and Service belong to the same Application and must be reconciled together, rather than being unrelated YAML files applied independently by a client.

* **Even without hooks or sync waves, Argo CD improves API-level correctness and consistency, but does not enforce runtime readiness by default.**
  Before sending any request to the API server, Argo CD computes a deterministic execution plan using phase, kind, and name ordering. This guarantees repeatable and predictable API application across syncs and environments. However, Argo CD still considers API acceptance as completion, so workloads may start before policies, quotas, or other behavioral guarantees are fully in effect. Enforcing such readiness boundaries requires explicit mechanisms such as hooks or Sync Waves.

> **Argo CD improves *how* resources are applied, not *when* their behavior becomes effective.**

---

### **1. Resources created via kubectl (client-driven model)**

When Kubernetes resources are created without Argo CD, they are typically applied using a direct client such as `kubectl`:

```bash
kubectl apply -f .
```

In this model:

* Manifests are submitted to the Kubernetes API server in **filename order** (or document order when using `---`)
* Each resource is validated and persisted **independently by the API server**
* There is **no dependency resolution or orchestration**
* There is **no waiting for runtime readiness or controller enforcement**

**Ordering behavior:**

*Multiple files*

```
1.yaml → 7.yaml → 9.yaml
```

*Single YAML with `---`*

* Resources are sent in the **order they appear**
* The client does **not reorder**
* The client does **not wait** for effects to take place

The client (`kubectl`) has **no awareness** of:

* Application-level relationships between resources
* Runtime readiness or behavioral guarantees
* Controller reconciliation or enforcement timing
* System-level correctness beyond API acceptance

From the client’s perspective, the operation is complete once the API server accepts the request.

---

### **2. Resources created using Argo CD (control-plane–driven model)**

![Alt text](/images/7b.png)
When Argo CD is used, but **no Sync Hooks or Sync Waves are defined**, it introduces **structure, determinism, and repeatability beyond kubectl**, while still treating **API server acceptance as the completion signal**.

At the start of a Sync operation, Argo CD:

* Collects **all manifests** belonging to an Application
* Builds a **single execution plan** for the entire Application
* Orders resources **deterministically**
* Submits API requests to the Kubernetes API server in that order

According to the Argo CD execution model, resource ordering follows this precedence:

1. **Phase**
2. **Sync Wave** (lower values first)
3. **Resource Kind**
4. **Resource Name**

> **Important clarification:**
> Although phase and sync wave are part of the ordering model, **we are intentionally not using hooks or sync waves yet**.
> At this point, ordering is driven entirely by **resource kind and resource name**.

---

#### **Default sequencing by resource kind**

Argo CD does not apply manifests arbitrarily. It uses a **kind-aware comparator** as part of its sync execution model to **reduce obvious Kubernetes API rejections** during a sync.

**Guiding principle:**

> **Resources that define scope or schema are applied before resources that depend on them.**

In practice, Argo CD’s built-in comparator **tends to place certain foundational resource types first**, most notably:

* **Namespaces**, which must exist before any namespaced resources
* **CustomResourceDefinitions (CRDs)**, which must exist before Custom Resources can be accepted

Beyond these foundational cases, Argo CD does **not provide a guaranteed, end-to-end dependency ordering for all Kubernetes resource kinds**.

**Typical kind-level ordering (illustrative, not exhaustive):**

* Namespaces
* CustomResourceDefinitions (CRDs)
* Other cluster-scoped resources
* Namespaced resources of various kinds (ConfigMaps, Secrets, ServiceAccounts, workloads, Services, etc.)

> **Important note:**
> This ordering reflects Argo CD’s *default intent* to avoid API-level failures such as “namespace not found” or “CRD does not exist.”
> It is **not a strict or documented contract**, and Argo CD does **not** guarantee a precise or semantically meaningful order among most namespaced resources.

---

**Example:**

```
Namespace app1-ns
CRD foos.example.com
ConfigMap app1-config
Deployment app1
```

Applied as:

```
Namespace → CRD → ConfigMap → Deployment
```

This avoids API failures like creating a Deployment in a non-existent Namespace or creating Custom Resources before their CRDs exist.


**Important boundary:**

> **Kind-based ordering guarantees API acceptance, not application intent, dependency correctness, or runtime behavior.**

Argo CD does **not** infer relationships such as:

* NetworkPolicies needing to exist before Deployments
* Guardrail resources needing to precede workloads
* One application tier (backend) needing to be fully applied before another (frontend)

All such resources are treated as **peers once they are namespaced**, unless additional orchestration mechanisms are introduced.

---

#### **Sequencing by name (final tie-breaker)**

When multiple resources share the same phase, wave (or no wave), and kind, Argo CD applies them in **alphabetical order by resource name**.

**Examples (pure name ordering, no implied dependency):**

```
configmap-a → configmap-b
deployment-1 → deployment-2
```

This ordering exists **only to make sync behavior deterministic and repeatable**.
It **does not represent dependency, priority, or application intent**, and must never be relied on to enforce correctness or sequencing guarantees.

---

### **Critical takeaway**

> **Kind and name ordering provide deterministic API application, not application correctness.**

At this stage:

* Kubernetes may accept resources even when higher-level intent is not yet satisfied
* Argo CD considers a resource “applied” once the API server accepts it
* No additional readiness or dependency guarantees are enforced by default

This distinction is foundational for understanding **why Sync Waves exist**, which we will address next.

---


## Why Sync Waves?

![Alt text](/images/7c.png)

During a Sync operation, Argo CD applies all manifests belonging to an Application as part of a **single synchronization cycle**.
If no additional controls are defined, Argo CD relies entirely on its **default ordering rules** based on phase, kind, and resource name.

This default ordering is designed to prevent **API-level failures**, not to encode application architecture or deployment intent.
At this point, it becomes important to distinguish between **two very different types of dependencies**.

---

#### 1) Explicit dependencies (Kubernetes-enforced)

Explicit dependencies are those that **Kubernetes itself enforces** at resource creation time.
If these dependencies are missing, the API server or kubelet **rejects or blocks workload creation**.

Because failures are surfaced immediately, **Argo CD’s default ordering and reconciliation are sufficient**, even without Sync Waves.
Kubernetes correctness guarantees ensure the workload cannot progress until prerequisites exist.

**Examples:**
A Deployment referencing a missing ServiceAccount, Secret, or ConfigMap will fail to create Pods until those objects exist.

---

#### 2) Implicit dependencies (intent-based, not enforced)

Implicit dependencies are **not enforced by Kubernetes** and represent **assumptions about ordering and intent**.
Kubernetes allows resources to be created in any order, even when that order violates operational expectations.

Because no API error occurs, Argo CD has **no signal** that the ordering is incorrect.
All resources may be applied successfully within the same sync window, despite the system being logically wrong.

**Examples:**
A Deployment can start Pods before a ResourceQuota exists or before a Service is created, even though both are expected beforehand.

---

## Ordering challenges without Sync Waves

**Example 1: NetworkPolicy and Deployment**

An Application may include a NetworkPolicy and a Deployment whose Pods must never start without that policy existing.

With default ordering:

* Both resources are part of the same synchronization cycle
* Both are namespaced objects
* There is no ordering rule that enforces NetworkPolicy creation before Deployment

From a resource creation perspective, Argo CD treats both objects as peers.
The Deployment can be created before or alongside the NetworkPolicy.

The API server accepts both objects successfully, but the assumption that “policy must exist before workload” is not represented anywhere.
This is an **ordering expressiveness gap**, not a reconciliation or controller problem.

---

**Example 2: ResourceQuota and workload creation**

An Application may contain a ResourceQuota and one or more Deployments within the same Namespace.

With default ordering:

* ResourceQuota and Deployment are independent resources
* There is no rule requiring the quota to exist before workloads
* Both objects can be submitted during the same sync cycle

As a result, workloads may be created in a namespace **before quota constraints exist at all**.
Nothing fails at the API level, but the intended deployment sequence is not enforced.

Again, this is a **resource creation ordering issue**, not a controller delay or reconciliation concern.

---

**Example 3: Implicit ordering between application components**

Consider an Application that defines multiple logical components, such as a **backend** and a **frontend**, within the same repository or Argo CD Application.

Each component has its own set of resources:
ConfigMaps, Services, Deployments, and policies.
The frontend implicitly assumes that the backend is already deployed and reachable.

Default ordering ensures the Namespace exists, but **does not impose ordering among namespaced resources**.
From Argo CD’s perspective, all namespaced objects are peers.

As a result:

* Backend and frontend resources may be created in the same synchronization cycle
* Frontend Deployments may start before backend Deployments exist
* There is no guarantee that all backend resources are applied before frontend resources

This violates a very common architectural assumption:

> “Deploy the backend first, then deploy the frontend.”

Argo CD has **no visibility into component-level intent** unless that intent is explicitly expressed.

> **Critical Note:**
> **Note:** These are just **three representative examples**. With the understanding built so far, you can easily imagine many more scenarios where default ordering is technically valid but operationally incorrect.

---

## What Sync Waves are and how they work

![Alt text](/images/7d.png)

**Sync Waves** are Argo CD’s mechanism for expressing **intent-aware ordering** when applying resources that belong to a **single Application**, specifically **inside the Sync phase**.

Up to this point, we’ve seen that Argo CD’s default ordering based on phase, kind, and name is designed to ensure **API-level correctness**, not to capture **application-specific intent**.
All resources that pass API validation may be created in the same synchronization cycle, even when the application logically expects clear boundaries between them.

Sync Waves exist to solve exactly this gap.

At a high level:

> **Sync Waves allow you to explicitly define which resources must be applied first, which must come next, and which must wait, instead of relying on implicit default ordering.**

Sync Waves are defined using the annotation:

```yaml
argocd.argoproj.io/sync-wave: "<integer>"
```

The rules are intentionally simple and predictable:

* The value is an integer
* Lower values are applied first
* Higher values are applied later
* Negative values are allowed
* Resources without a sync-wave default to `0`

When a Sync operation runs, Argo CD:

* Collects **all manifests** belonging to the Application
* Orders them using the full execution precedence:

  * Phase
  * Sync Wave (lowest to highest)
  * Resource Kind
  * Resource Name
* Applies resources strictly in that computed order

This is the critical distinction:

> **Default ordering answers “can this object be created?”
> Sync Waves answer “should this object be created now?”**

Sync Waves operate:

* **Only within a single Application**
* **Only during the Sync phase**

They do not span Applications, and they do not introduce new lifecycle phases. They simply give structure and intent to the ordering **where default rules fall short**.

---

## How Argo CD determines the final resource order

When Argo CD performs a Sync, it evaluates **all manifests belonging to an Application** and computes a single execution plan.

If **no hooks are defined**, all manifests implicitly belong to the **Sync phase**, and ordering is determined entirely by **Sync Waves (if present), resource kind, and resource name**.

According to the Argo CD execution model, resource ordering follows this precedence:

1. **Phase**
2. **Sync Wave** (lower values first)
3. **Resource Kind**
4. **Resource Name**

In practice, Argo CD resolves ordering by progressively narrowing down precedence:

* First, lifecycle phase (only relevant if hooks exist)
* Then, sync waves within the Sync phase
* Then, kind-based ordering
* Finally, name-based ordering as a tie-breaker

Only after all four dimensions are resolved are requests sent to the Kubernetes API server.

---

## How Sync Waves influence ordering in practice

Sync Waves operate **only inside the Sync phase** and are used to express **application-level ordering intent** that default ordering cannot infer.

Important behaviors to understand:

* Resources that define a `sync-wave` participate in wave-based ordering
* Resources **without** a `sync-wave` implicitly default to **wave `0`**
* Wave ordering is applied **before** kind and name ordering
* Kind and name ordering are still applied **within the same wave**

This means Sync Waves do not replace default ordering, they **sit on top of it** and give you a higher-level grouping mechanism.

---

## Where hooks fit

Hooks exist in **separate lifecycle phases** and are evaluated **outside the Sync phase**.

What this implies:

* PreSync hooks always run **before** any Sync-phase resources
* Sync Waves are **not evaluated for hooks**
* Hooks control *when logic executes*
* Sync Waves control *how resources are sequenced*

If hooks are not used, phases effectively collapse into Sync, and **waves become the primary ordering mechanism** beyond kind and name.

---


# Demo: Argo CD Sync Waves

In this demo, we will **demonstrate Argo CD Sync Waves** by deploying a simple but realistic Kubernetes application and explicitly controlling **the order in which resources are created**.

The goal is to clearly understand:

* Which dependencies are **explicit and enforced by Kubernetes**
* Which dependencies are **implicit and intent-based**
* Why **Sync Waves are required only for the latter**

---

## What are we going to do?

We will deploy an application called **app1** using Argo CD.

This application is composed of the following Kubernetes resources:

* Namespace
* ResourceQuota
* ServiceAccount
* Secret
* ConfigMap
* Service
* Deployment

These resources are **logically related**, but Kubernetes does **not enforce a complete creation order** across all of them.

This demo shows how to **declare application intent explicitly using Sync Waves**, instead of relying on assumptions.


> **Note on dependencies**
>
> * **Explicit dependencies (Kubernetes-enforced):** Namespace, ServiceAccount, Secret, and ConfigMap are required for Pod creation. If missing, Kubernetes rejects or blocks workloads. **Argo CD’s default sync behavior already orders and reconciles these correctly even when Sync Waves are not used**, relying on Kubernetes validation, retries, and reconciliation.
> * **Implicit dependencies (intent-based):** ResourceQuota and Service are not enforced by Kubernetes at creation time. Pods can start before they exist, leading to incorrect system behavior. **Sync Waves are required to explicitly enforce this intent**.


## Deployment Intent and Sync Wave Plan

For this application, the deployment intent is very clear. While Kubernetes allows most resources to be created in any order, **this application expects a specific sequence** to ensure governance, identity, and configuration are enforced correctly.

### Intent we want to enforce

* The Namespace must exist first
* Governance and identity primitives must be created early
* Configuration and secrets must exist before workloads
* ResourceQuota must be enforced **before any Pods start**
* The Service should exist before traffic reaches Pods
* The Deployment must be created last

We will **not rely on default kind ordering**.
We will **declare this intent explicitly using Sync Waves**.

---

### Sync Wave execution plan

The table below defines the **exact execution order** Argo CD should follow, along with the **type of dependency** each resource represents.

| Resource       | Purpose                 | Dependency Type | Sync Wave |
| -------------- | ----------------------- | --------------- | --------- |
| Namespace      | Isolation boundary      | Explicit        | `-2`      |
| ResourceQuota  | Governance guardrail    | Implicit        | `-1`      |
| ServiceAccount | Workload identity       | Explicit        | `-1`      |
| Secret         | Sensitive configuration | Explicit        | `-1`      |
| ConfigMap      | Application config      | Explicit        | `0`       |
| Service        | Stable access endpoint  | Implicit        | `1`       |
| Deployment     | Application workload    | —               | `5`       |

This plan intentionally uses:

* **Negative waves** for foundations and guardrails
* **Zero wave** for baseline configuration
* **Positive waves** for runtime workloads

This mirrors how real production systems are designed, where **policy and governance must precede execution**.

> **Note on Sync Wave numbering**
> The gap between sync wave values (for example, `1` for Service and `5` for Deployment) is intentional. Leaving gaps provides flexibility to introduce additional resources in the future, such as NetworkPolicies, PodDisruptionBudgets, or other guardrails, without having to renumber existing Sync Waves.
> Always plan Sync Wave integers with **future growth and extensibility** in mind.


> **Note on LimitRange**
> In production environments, a `LimitRange` is typically defined alongside a `ResourceQuota` at the namespace level to ensure Pods that do not specify resource requests and limits automatically receive defaults.
> In this demo, we intentionally **do not define a LimitRange** for simplicity and instead **explicitly set resource requests and limits in the Deployment** to make quota behavior clear and easy to reason about.

---

## Demo prerequisites

### 1) Argo CD must be running and UI accessible

If you installed Argo CD as part of **Lecture 02**, ensure port-forwarding is active.

```bash
kubectl port-forward -n argocd svc/my-argo-cd-argocd-server 8080:443
```

Open the UI at:

```
https://localhost:8080
```

---

### 2) Ensure a clean environment

Make sure the namespace `app1-ns` does **not** exist from previous demos.

This ensures we can clearly observe:

* Namespace creation
* Guardrail enforcement
* Sync Wave execution

---

## Step 1: Create the Argo CD Application

The Argo CD Application manifest for this demo is located at:

```
app1-config/argo/app1-app-crd.yaml
```

Apply it:

```bash
kubectl apply -f app1-app-crd.yaml
```

### Notes

* Update the `repoURL` to point to **your GitHub account and repository**
* At this stage, the repo and manifests may not exist yet

### Expected UI behavior

In the Argo CD UI:

* The Application appears in **Yellow or Red**
* Sync status indicates missing or unreachable manifests

This is expected.

---

## Step 2: Create the Git repository

To keep the demo focused on Sync Waves, we will use a **public repository**.

For private repo authentication, refer to **Lecture 04**:

```
https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/04-PrivateRepo%2BSyncPruneSelfHeal
```

### Repository layout

Create a public repository named `app1-config` and add:

```
app1-config/
├── argo/
│   └── app1-app-crd.yaml
└── config/
    ├── 01-ns.yaml
    ├── 02-resourcequota.yaml
    ├── 03-sa.yaml
    ├── 04-cm.yaml
    ├── 05-secret.yaml
    ├── 06-deployment.yaml
    └── 07-svc.yaml
```

Commit and push the changes.

---

## Step 3: Perform a manual sync

Now observe Sync Waves in action.

1. Open the **Argo CD UI**
2. Select the `app1` Application
3. Click **Synchronize**
4. Leave defaults unchanged
5. Click **Sync**

### What to observe

* Resources are **not created simultaneously**
* Lower sync waves complete first
* ResourceQuota is applied before Pods exist
* Deployment waits for all earlier waves

This confirms that **application intent, not API acceptance, is driving execution**.

---

## Step 4: Access the application

Once the Application is **Healthy and Synced**, access the app:

```bash
kubectl port-forward -n app1-ns svc/app1-service 8081:80
```

Open:

```
http://localhost:8081
```

You should see the nginx page served from the ConfigMap.

---

## Key takeaway

This demo proves that:

* Kubernetes enforces **explicit dependencies**
* Argo CD already handles those by default
* ResourceQuota and Service are **implicit dependencies**
* Sync Waves exist to express **human intent**
* Production-grade GitOps requires declared ordering

> Sync Waves do not change what is deployed.
> They change **when** things are deployed.

---

## Conclusion

Kubernetes guarantees **API correctness**, not **application correctness**.
Argo CD improves upon raw client-driven models by introducing deterministic, repeatable application of manifests, but its default behavior still focuses on API acceptance rather than runtime intent.

The distinction between **explicit dependencies** and **implicit dependencies** is the key mental model:

* Explicit dependencies are enforced by Kubernetes and handled safely by Argo CD by default
* Implicit dependencies represent architectural and operational intent that Kubernetes does not enforce

**Sync Waves exist to bridge this gap.**

By allowing administrators to define explicit, integer-based ordering within a lifecycle phase, Sync Waves make application intent **declarative, visible, and reproducible**. They ensure that guardrails, policies, and architectural assumptions are respected consistently across environments.

In production-grade GitOps systems, correctness is not accidental.
It is **designed**, **declared**, and **enforced**—and Sync Waves are a critical part of that design.

---

## References

* Kubernetes API Concepts
  [https://kubernetes.io/docs/concepts/overview/kubernetes-api/](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)

* Kubernetes Object Management
  [https://kubernetes.io/docs/concepts/overview/working-with-objects/](https://kubernetes.io/docs/concepts/overview/working-with-objects/)

* Argo CD Official Documentation
  [https://argo-cd.readthedocs.io/](https://argo-cd.readthedocs.io/)

* Argo CD Sync Waves
  [https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)

* Argo CD Hooks and Lifecycle Phases
  [https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/)

---

