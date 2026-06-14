# Argo CD Helm Tutorial | Hands-On Step-by-Step Demo

## Video reference for this lecture is the following:

[![Watch the video](https://img.youtube.com/vi/yyQgK1DeOkA/maxresdefault.jpg)](https://www.youtube.com/watch?v=yyQgK1DeOkA&ab_channel=CloudWithVarJosh)

---
## ⭐ Support the Project  
If this **repository** helps you, give it a ⭐ to show your support and help others discover it! 

---

## Table of Contents

* [Introduction](#introduction)  
* [Helm Charts and Argo CD](#helm-charts-and-argo-cd)  
  * [How Argo CD uses Helm](#how-argo-cd-uses-helm)  
  * [Where this fits in the Argo CD architecture](#where-this-fits-in-the-argo-cd-architecture)  
  * [Helm chart sources supported by Argo CD](#helm-chart-sources-supported-by-argo-cd)  
  * [Why use Helm with Argo CD?](#why-use-helm-with-argo-cd)  
  * [Key takeaway](#key-takeaway)  
* [Demo: Argo CD and Helm](#demo-argo-cd-and-helm)  
  * [Demo prerequisites](#demo-prerequisites)  
  * [Demo Introduction: What We’re Going to Do](#demo-introduction-what-were-going-to-do)  
  * [Step 1: Understand the directory structure](#step-1-understand-the-directory-structure)  
  * [Step 2: Create and understand the Argo CD Application](#step-2-create-and-understand-the-argo-cd-application)  
  * [Using multiple values files (environment-specific)](#using-multiple-values-files-environment-specific)  
  * [Step 3: Create the Git repository](#step-3-create-the-git-repository)  
  * [Step 4: Observe behavior in Argo CD UI](#step-4-observe-behavior-in-argo-cd-ui)  
  * [Step 5: Access the application](#step-5-access-the-application)  
  * [Key takeaway](#key-takeaway-1)  
* [Conclusion](#conclusion)  
* [References](#references)  

---

## Introduction

Helm and Argo CD are two widely used tools in Kubernetes environments, but they serve **very different purposes**.
Confusion often arises when teams assume that Argo CD uses Helm as a deployment engine in the same way Helm is used manually.

This write-up clarifies that boundary.

You will learn how Argo CD integrates with Helm, what actually happens when a Helm chart is used as an application source, and why Helm remains valuable even when Argo CD owns deployment, reconciliation, and rollback.

The included demo intentionally keeps templating simple, allowing you to focus on **GitOps behavior, lifecycle ownership, and rendering boundaries**, which are critical concepts for production-grade Argo CD usage.

---

## Helm Charts and Argo CD

When Argo CD manages a Helm chart, Helm is **not** used as a deployment or lifecycle engine.
Argo CD does **not** execute `helm install`, `helm upgrade`, `helm rollback`, or `helm uninstall`.

Instead, Helm is used **exclusively to render Kubernetes manifests**.

This separation of responsibilities is intentional and foundational to GitOps workflows with Argo CD.

---

### How Argo CD uses Helm

When a Helm chart is configured as an application source, Argo CD uses Helm only for **template rendering**.

The flow is as follows:

* Reads `Chart.yaml`, templates, and selected values files
* Executes an equivalent of `helm template`
* Produces plain Kubernetes YAML manifests
* Applies those manifests using the Kubernetes API
* Continuously reconciles live state against Git

Because Helm is used only for rendering:

* No Helm release is created in the cluster
* No Helm release metadata or history exists
* No Helm-based rollback is possible

All lifecycle control, reconciliation, and rollback behavior is handled entirely by **Argo CD**, with **Git as the source of truth**.

---

### Where this fits in the Argo CD architecture

Relating this to the Argo CD architecture covered in **Lecture 02**:

* **Repository Server**

  * Fetches the Helm chart from the Git repository
  * Renders manifests by running `helm template`

* **Application Controller**

  * Applies the rendered manifests to the cluster
  * Monitors and reconciles drift between Git and live state

Once rendering is complete, Helm plays no further role.
From Argo CD’s perspective, rendered output is indistinguishable from raw Kubernetes YAML.

---

### Helm chart sources supported by Argo CD

Argo CD supports Helm charts from multiple sources:

* **Custom charts** maintained by your teams
* **Public charts** provided by upstream projects and vendors

Regardless of the source, the execution model remains the same:
Helm renders manifests, and Argo CD manages deployment and reconciliation.

---

### Why use Helm with Argo CD?

If Argo CD manages deployment and lifecycle, Helm’s value lies in **managing configuration complexity**, not deployment.

As applications scale, raw Kubernetes YAML becomes harder to manage due to:

* Environment-specific configuration differences
* Repeated boilerplate across services
* Optional features and conditional resources
* Large, difficult-to-maintain manifest sets

Helm addresses these problems by providing:

* Parameterization through values files
* Reusable and composable templates
* A consistent structure for complex applications
* The industry-standard packaging format for Kubernetes software

Argo CD then applies GitOps principles on top of the rendered output, ensuring correctness, drift detection, and controlled rollouts.

---

### Key takeaway

> With Argo CD, Helm is a **manifest generation tool**, not a deployment tool.
> Deployment, reconciliation, and rollback are owned by Argo CD and driven by Git.

This clear division of responsibility is what enables Helm and Argo CD to work effectively together in production GitOps environments.

---


# Demo: Argo CD and Helm

In this demo, we will understand **how Argo CD works with Helm charts**, and more importantly, **what Argo CD does and does not do when Helm is used as the application source**.

This demo intentionally keeps the Helm chart simple so that the focus remains on **Argo CD behavior**, not Helm templating.

---

## Demo prerequisites

### 1) Argo CD must be running and UI accessible

If you installed Argo CD as part of **Lecture 02**, ensure port-forwarding to the Argo CD API server is active.

```bash
kubectl port-forward -n argocd svc/my-argo-cd-argocd-server 8080:443
```

Open the UI in your browser:

```
https://localhost:8080
```

---

### 2) Basic understanding of Helm

This demo assumes you already understand **Helm basics** such as:

* Charts
* Templates
* Values files
* Rendering behavior

If you need a refresher, I have already covered Helm from **Basics to Production** on this channel with multiple demos.

**GitHub notes:**: [https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2043](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2043)  
**YouTube video:**: [https://www.youtube.com/watch?v=yvV_ZUottOM](https://www.youtube.com/watch?v=yvV_ZUottOM)

---

### 3) Ensure a clean environment

Make sure the namespace `app1-ns` does **not** exist from previous demos.

```bash
kubectl get ns app1-ns
```

If it exists, delete it before proceeding.

---

## Demo Introduction: What We’re Going to Do

In this demo, we will deploy a simple application called **app1** using **Argo CD with a Helm chart as the source**.

The focus is not on learning Helm, but on understanding **how Argo CD uses Helm charts** and where responsibility boundaries exist.

We will:

* Use a Helm chart to define basic Kubernetes resources
* Configure an Argo CD Application to reference the chart
* Observe how Argo CD renders templates and applies manifests
* Verify that Argo CD manages deployment without creating Helm releases
* Access the application to validate end-to-end behavior

By the end of the demo, you should clearly understand **Helm’s role in a GitOps workflow with Argo CD**, which prepares us for **App-of-Apps** and larger production setups.

---

## Step 1: Understand the directory structure

For this demo, we will use the following repository structure:

```
app1-config
├── app1-helm
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates
│       ├── 01-namespace.yaml
│       ├── 02-configmap.yaml
│       ├── 03-service.yaml
│       └── 04-deployment.yaml
└── argo
    └── app1-app-crd.yaml
```

### Key points to understand

* `app1-helm/`
  Contains the **Helm chart**, including templates and values.
* `templates/`
  Holds standard Kubernetes manifests rendered by Helm.
* `argo/`
  Contains the **Argo CD Application CRD** that points to the Helm chart.
* All files required for this demo are already part of the **lecture notes repository**, under the directory `app1-config`.

---

## Step 2: Create and understand the Argo CD Application

Reference documentation:
[https://argo-cd.readthedocs.io/en/latest/user-guide/helm/](https://argo-cd.readthedocs.io/en/latest/user-guide/helm/)

The Argo CD Application manifest for this demo is located at:

```
app1-config/argo/app1-app-crd.yaml
```

### Application manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/CloudWithVarJosh/app1-config.git
    targetRevision: HEAD
    path: app1-helm
    helm:
      releaseName: app1
  destination:
    server: https://kubernetes.default.svc
    namespace: app1-ns
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

### Understanding the `helm.releaseName` block

```yaml
helm:
  releaseName: app1
```

This block controls the **Helm release name at render time**, which is required whenever Helm templates are rendered.

---

### Helm template syntax (important context)

The basic Helm render command looks like this:

```bash
helm template <release-name> <chart-path>
```

For example:

```bash
helm template app1 ./
```

* `app1` is the **Helm release name**
* `./` points to the **Helm chart directory**

  * The directory must contain `Chart.yaml`
  * Helm reads templates and values relative to this path

Helm does **not** deploy anything in this mode. It only renders YAML.

---

### How Argo CD uses this internally

When you configure an Argo CD Application with:

```yaml
path: app1-helm
helm:
  releaseName: app1
```

Argo CD’s **Repository Server** performs the equivalent of:

```bash
cd app1-helm
helm template app1 ./
```

Important implications:

* The `path` field decides **where Helm runs**
* The `./` is always relative to the chart directory
* The chart **must** exist exactly at the specified path

If the directory structure changes:

* `path` must be updated accordingly
* Otherwise, rendering fails because `Chart.yaml` is not found

---

### How `releaseName` is used in templates

The release name is exposed to Helm templates using:

```yaml
{{ .Release.Name }}
```

In this demo:

* Resource names (Deployment, Service, ConfigMap) use `.Release.Name`
* This makes rendered manifests **explicit and predictable**
* Naming becomes consistent across environments

---

### What if `releaseName` is not supplied?

If the `helm.releaseName` block is omitted:

* Argo CD **auto-generates** a release name
* Rendering still succeeds
* `.Release.Name` is still populated
* The generated name is typically derived from the **Argo CD Application name**

However:

* Resource names may become **less predictable**
* Multi-instance deployments become harder to reason about

---

### Why explicitly setting `releaseName` is recommended

Explicitly setting `releaseName` is considered **production-friendly** because:

* Resource naming is deterministic
* Templates using `.Release.Name` are easier to reason about
* Multiple instances of the same chart can coexist cleanly

This approach aligns well with **GitOps practices**, where clarity and predictability are more important than convenience defaults.

---

### Using multiple values files (environment-specific)

If you’ve watched my **Helm lecture** and followed the **multiple environments demo** (for example `dev`, `stage`, and `prod`), you might naturally ask:

> How does this work when Argo CD is deploying a Helm chart that contains multiple `values.yaml` files?

In Argo CD, environment selection is **explicit** and happens at the **Application level**.

Argo CD does **not** automatically choose or merge values files.
The Application CRD must clearly specify **which values file to use**.

---

#### Helm chart structure with multiple environments

Assume the Helm chart directory contains the following files:

```
values-dev.yaml
values-stage.yaml
values-prod.yaml
```

Each file represents configuration for a specific environment.

---

#### Production Application example

For a **production** Argo CD Application, the Application CRD references **only** the production values file:

```yaml
source:
  helm:
    valueFiles:
      - values-prod.yaml
```

**Behavior:**

* Only `values-prod.yaml` is used during rendering
* `values-dev.yaml` and `values-stage.yaml` are ignored
* The same chart and templates are reused across environments

---

#### Staging Application example

Similarly, a **staging** Application explicitly selects the staging values file:

```yaml
source:
  helm:
    valueFiles:
      - values-stage.yaml
```

Each environment is represented by a **separate Argo CD Application**, which is the documented and recommended GitOps approach.

---

#### How Argo CD processes values files

Internally, Argo CD passes the specified values files directly to Helm’s rendering step.
The behavior is equivalent to running:

```bash
helm template <release-name> ./ -f values-prod.yaml
```

Important points:

* No implicit environment detection
* No automatic values merging
* No values file is used unless explicitly listed
* Rendering behavior is deterministic and Git-driven

This behavior aligns with the official Argo CD Helm documentation:
[https://argo-cd.readthedocs.io/en/latest/user-guide/helm/](https://argo-cd.readthedocs.io/en/latest/user-guide/helm/)


### Apply the Application

```bash
kubectl apply -f app1-app-crd.yaml
```

#### Notes

* Update `repoURL` to point to **your GitHub account and repository**
* At this moment, the repository or manifests may not yet exist

#### Expected UI behavior

In the Argo CD UI:

* The Application appears in **Yellow or Red**
* Sync status shows missing or unreachable manifests

This is expected and correct.

---

## Step 3: Create the Git repository

To keep this demo focused on **Helm and Argo CD**, we will use a **public GitHub repository**.

For private repository authentication, refer to **Lecture 04**:
[https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/04-PrivateRepo%2BSyncPruneSelfHeal](https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/04-PrivateRepo%2BSyncPruneSelfHeal)

### Repository setup

1. Create a public repository named:

```
app1-config
```

2. Add the following two directories **without changing their parent structure**:

```
app1-config
├── app1-helm
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates
│       ├── 01-namespace.yaml
│       ├── 02-configmap.yaml
│       ├── 03-service.yaml
│       └── 04-deployment.yaml
└── argo
    └── app1-app-crd.yaml
```

3. Commit and push the changes.

---

## Step 4: Observe behavior in Argo CD UI

Since the Application was previously in an error state due to missing manifests, once the repository is populated:

* Argo CD automatically detects the changes
* Helm templates are rendered
* Resources are applied automatically because **auto-sync is enabled**

You should see the Application transition to:

* **Synced**
* **Healthy**

---

## Step 5: Access the application

Once the Application is healthy and synced, access the application using port forwarding:

```bash
kubectl port-forward -n app1-ns svc/app1-service 8081:80
```

Open your browser:

```
http://localhost:8081
```

You should see the **nginx page served from the ConfigMap**, confirming that:

* Helm templates were rendered correctly
* Argo CD applied the manifests
* The application is running as expected

---

## Key takeaway

This demo demonstrates that:

* Argo CD uses Helm only to **render manifests**
* Helm does **not** manage deployment lifecycle
* No Helm release or history exists in the cluster
* Git and Argo CD together provide the complete GitOps lifecycle

This understanding is foundational before moving on to **App-of-Apps** and **Mega Projects**.


---

## Conclusion

In this section and demo, we established a clear and correct mental model for using Helm with Argo CD.

Key points to remember:

* Argo CD does **not** use Helm to manage deployment lifecycle
* Helm is used **only to render Kubernetes manifests**
* No Helm release, history, or rollback exists in the cluster
* Git remains the single source of truth
* Argo CD owns application state, reconciliation, and rollback

Understanding this separation is essential before moving on to more advanced patterns such as **multiple environments**, **App-of-Apps**, and **large-scale GitOps mega projects**.

Once this boundary is clear, Helm and Argo CD work together cleanly, predictably, and safely in production environments.

---

## References

Official documentation and authoritative resources used in this lecture and demo:

* Argo CD Helm Integration
  [https://argo-cd.readthedocs.io/en/latest/user-guide/helm/](https://argo-cd.readthedocs.io/en/latest/user-guide/helm/)

* Argo CD Architecture Overview
  [https://argo-cd.readthedocs.io/en/latest/operator-manual/architecture/](https://argo-cd.readthedocs.io/en/latest/operator-manual/architecture/)

* Helm Documentation
  [https://helm.sh/docs/](https://helm.sh/docs/)

* Helm Template Command Reference
  [https://helm.sh/docs/helm/helm_template/](https://helm.sh/docs/helm/helm_template/)

* GitOps Principles (CNCF)
  [https://opengitops.dev/](https://opengitops.dev/)

---