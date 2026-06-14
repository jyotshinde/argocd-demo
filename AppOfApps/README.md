# Argo CD App of Apps Explained | Sync Options | Hands-On GitOps Demo

## Video reference for this lecture is the following:

[![Watch the video](https://img.youtube.com/vi/01chRZSZFcY/maxresdefault.jpg)](https://www.youtube.com/watch?v=01chRZSZFcY&ab_channel=CloudWithVarJosh)

---
## ⭐ Support the Project  
If this **repository** helps you, give it a ⭐ to show your support and help others discover it! 

---

## Table of Contents

- [Introduction](#introduction)  
- [Critical Note on Terminology](#critical-note-on-terminology)  
- [Why App of Apps Is Needed](#why-app-of-apps-is-needed)  
- [What Is App of Apps](#what-is-app-of-apps)  
- [How App of Apps Works](#how-app-of-apps-works)  
- [Why App of Apps Matters](#why-app-of-apps-matters)  
- [Demo: App of Apps (Argo CD)](#demo-app-of-apps-argo-cd)  
  - [Demo Introduction: What Are We Going to Do](#demo-introduction-what-are-we-going-to-do)  
  - [Demo Prerequisites](#demo-prerequisites)  
  - [Step 1: Understand the Directory Structure](#step-1-understand-the-directory-structure)  
  - [Step 2: Build and Push Container Images](#step-2-build-and-push-container-images)  
  - [Step 3: Understand the Child Argo CD Applications (FE & BE)](#step-3-understand-the-child-argo-cd-applications-fe--be)  
  - [Step 4: Create Git Repositories](#step-4-create-git-repositories)  
  - [Step 5: Create and Apply the Parent Application (App of Apps)](#step-5-create-and-apply-the-parent-application-app-of-apps)  
  - [Step 6: Observe Behavior in the Argo CD UI](#step-6-observe-behavior-in-the-argo-cd-ui)  
  - [Step 7: Access the Application](#step-7-access-the-application)  
  - [Step 8: Deletion and Self-Healing Behavior](#step-8-deletion-and-self-healing-behavior)  
- [Conclusion](#conclusion)  
- [References](#references) 

---

## Introduction

This lecture focuses on the **App of Apps pattern in Argo CD**, a commonly used GitOps approach for managing complex products composed of multiple components.

As products evolve beyond single deployments into **tiered architectures or microservices**, the number of Argo CD Applications grows rapidly. While Argo CD handles individual Applications very well, operating an entire product made up of many Applications introduces new challenges around visibility, ownership, and orchestration.

In this lecture, you will:

* Understand **why the App of Apps pattern exists**
* Learn **what problem it solves** in real-world GitOps setups
* See **how it works conceptually and operationally**
* Implement the pattern end-to-end using a **hands-on demo**

---

## App of Apps (Argo CD)

### Critical Note on Terminology

In this lecture, I will **intentionally avoid using the word *application*** when referring to what you are building.

The reason is simple:
the term **application** can refer to **two very different things** in this context.

* Your **actual system** (what end users consume)
* An **Argo CD Application** (a GitOps custom resource)

To avoid this ambiguity, I will refer to your actual system as a **product** or **software** throughout this lecture.

* **Product/Software** → what you are delivering and deploying
* **Argo CD Application** → a GitOps construct that deploys part of that product

Keeping this distinction clear is essential for correctly understanding the App of Apps pattern.

---

## Why App of Apps Is Needed

![Alt text](/images/9a.png)

Modern products are rarely deployed as a single, monolithic unit.
In practice, most real-world systems are designed either as **tiered architectures** or as **microservices-based systems**.

In a **tiered architecture**, a product is typically composed of components such as a **frontend**, **backend**, and **database**.
In a **microservices architecture**, the same product may consist of many independently deployable services such as **orders**, **web-ui**, **mobile-ui**, **api-gateway**, **wishlist**, **payments**, and more.

When following GitOps best practices, **each of these components is usually deployed as a separate Argo CD Application**.
This provides clear ownership, independent lifecycle management, and better isolation between components.

However, complexity increases quickly when environments are introduced.
Most teams run the same product across multiple environments such as **dev**, **stage**, and **prod**.
As a result, the number of Argo CD Applications grows multiplicatively.

For example:

* One product
* Multiple components (frontend, backend, services)
* Multiple environments (dev, stage, prod)

Very quickly, a **single product maps to many Argo CD Applications**.

#### Operational Challenges Without App of Apps

* **No Single Entry Point**
  There is no single Argo CD Application that represents the entire product. Operators must inspect multiple Applications individually to understand whether the product is fully deployed. This makes product-level operations harder to reason about and increases the chance of mistakes.

* **Fragmented Product Health**
  Each Argo CD Application exposes its own sync and health status in isolation. There is no consolidated view that clearly communicates the health of the product as a whole. As a result, partial failures can be difficult to detect and reason about.

* **Manual Product Composition**
  Argo CD does not inherently know which Applications together form a single product. Operators must mentally map frontend, backend, and other components to determine completeness. This knowledge often lives outside Git, making it harder to maintain and scale.

* **Complex Cluster Bootstrapping**
  Deploying the same product into a new cluster requires manually creating and configuring multiple Argo CD Applications. Missing even one Application can result in an incomplete or broken deployment, increasing operational risk and slowing down onboarding.

The **App of Apps pattern** addresses these challenges by introducing a **product-level abstraction**, allowing multiple Argo CD Applications to be managed together as a single logical unit.

---

## What Is App of Apps?

![Alt text](/images/9b.png)

**App of Apps is a GitOps pattern, not a feature.**

It is a pattern used to manage a **product or software composed of multiple Argo CD Applications** as a **single, declarative unit**.

In a typical GitOps setup, each component of a product (such as frontend, backend, or microservices) is deployed using a separate Argo CD Application. While this works well for individual components, Argo CD does not natively understand how multiple Applications together form one product.

The App of Apps pattern addresses this by introducing a **parent Argo CD Application** that represents the product (or a specific environment of the product).

The parent application:

* Declaratively defines **which Argo CD Applications belong to the product**
* Defines **where those Applications are sourced from in Git**
* Creates, tracks, and reconciles those Applications during sync

Instead of managing Applications one by one, you manage the **entire product as a single logical unit**.

---

## How App of Apps Works

The App of Apps pattern relies on a clear separation of responsibilities between Applications.

The **parent Argo CD Application** does **not** deploy Kubernetes workloads directly.
Its sole responsibility is to **manage other Argo CD Applications**.

Each **child Argo CD Application**:

* Manages Kubernetes resources such as Deployments, Services, and ConfigMaps
* Represents a specific component of the product
* Owns the lifecycle of that component

Together, these child Applications make up the product, while the parent Application acts as the **orchestration and control layer**.

In effect:

* The **parent manages Applications**
* The **child Applications manage workloads**
* Git defines both **product composition** and **desired state**

---

## Why App of Apps Matters

By introducing a parent Application, App of Apps solves several operational challenges:

* Provides a **single entry point** for product-level deployment
* Makes product composition **explicit and declarative in Git**
* Enables **product-level synchronization and reconciliation**
* Simplifies reasoning about product health and completeness

This pattern becomes increasingly valuable as the number of components and environments grows, but it can also be applied early to establish a clean and scalable GitOps model.

---

## Demo: App of Apps (Argo CD)

## Demo Introduction: What Are We Going to Do?

![Alt text](/images/9c.png)

In this demo, we will work with a **simple product composed of two tiers**:
a **frontend (FE)** and a **backend (BE)**.

Each tier will be deployed as its own **Argo CD Application**, backed by its own Git repository and Kubernetes manifests. Together, these two tiers will represent a single **product** that users interact with.

Instead of managing the frontend and backend Applications independently, we will introduce a **parent Argo CD Application** that represents the **entire product**. This parent application will act as the **single control point**, responsible for creating, synchronizing, and monitoring the child Applications for both tiers.

#### In this demo, we will:

* Build and deploy a **frontend and backend** as separate Argo CD Applications
* Use a **parent (root) Application** to manage both tiers together
* Pull Application definitions from **multiple Git repositories**
* Observe how **Git becomes the single source of truth** for the product
* See how Argo CD handles **synchronization, health, and self-healing** at the product level

#### What you should focus on while watching this demo:

* How a product is modeled as a **collection of Applications**
* How the parent application **creates and reconciles** child Applications
* How changes and deletions are handled automatically via GitOps
* How App of Apps simplifies operating even a small product

The objective here is **not complexity**, but clarity.
We deliberately keep the product small (frontend + backend) so that the **App of Apps flow is easy to follow**, while still reflecting how this pattern is used in real production environments.

> **Important Note:**
> You may not always see the App of Apps pattern used for small products with only a few Argo CD Applications, such as a simple frontend–backend setup.
>
> In many real-world teams, such products initially start without a parent application.
>
> In this demo, we intentionally apply the App of Apps pattern to a simple product so you can clearly understand how it works, before applying it to larger and more complex systems.

---

## Demo Prerequisites

Before starting the demo, ensure the following:

* Argo CD is installed and running
* Argo CD UI is accessible

If you installed Argo CD as part of **Lecture 02**, start port-forwarding:

```bash
kubectl port-forward -n argocd svc/my-argo-cd-argocd-server 8080:443
```

Access the UI at:

```
https://localhost:8080
```

Login using the credentials configured during installation.


>**Installing Argo CD:**
Follow the step-by-step guide here to install Argo CD locally using kind:
[https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/02-Arch-Install#lab-installing-argo-cd-local-setup-using-kind](https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/02-Arch-Install#lab-installing-argo-cd-local-setup-using-kind)

---

## Step 1: Understand the Directory Structure

Before we touch Argo CD, it is critical to understand **how the product is structured in Git**.

> All files required for this demo are already provided in the GitHub notes for this lecture.
> I strongly encourage you to follow along and perform this demo yourself.
> You learn GitOps best by doing.

### High-level structure

```
product1/
├── product1-be
│   ├── app.py
│   └── Dockerfile
├── product1-be-config
│   ├── argo
│   │   └── be-app.yaml
│   └── manifests
│       ├── deploy.yaml
│       └── svc.yaml
├── product1-fe
│   ├── app.py
│   └── Dockerfile
├── product1-fe-config
│   ├── argo
│   │   └── fe-app.yaml
│   └── manifests
│       ├── deploy.yaml
│       └── svc.yaml
└── product1-gitops
    └── product1-root.yaml
```

### What each directory represents

* **product1-be / product1-fe**

  * Application source code
  * Dockerfiles
  * Used only to build container images

* **product1-be-config / product1-fe-config**

  * GitOps repositories
  * Contain:

    * Argo CD Application CRDs
    * Kubernetes manifests

* **product1-gitops**

  * Product-level GitOps repository
  * Contains the **parent (App of Apps) Application**

> Notice the clear separation between **application code**, **GitOps configuration**, and **product orchestration**.

---

## Step 2: Build and Push Container Images

To keep this demo focused on **App of Apps**, we use simple Flask applications.

The application code, Dockerfiles, and manifests are already provided.
You only need to **build and push images using your own Docker Hub account**.

### Backend image

```bash
cd product1-be
docker build -t <your-dockerhub-username>/product1-be:v1.0.0 .
docker push <your-dockerhub-username>/product1-be:v1.0.0
```

### Frontend image

```bash
cd product1-fe
docker build -t <your-dockerhub-username>/product1-fe:v1.0.0 .
docker push <your-dockerhub-username>/product1-fe:v1.0.0
```

### Important notes (read carefully)

* You **do not need to write any code or Dockerfiles**
* Manifests default to `cloudwithvarjosh` Docker Hub account
* You **must**:

  * Use your own Docker Hub account
  * Update Deployment manifests to reference your image repository

If running on a Linux VM:

```bash
docker login
```

---

## Step 3: Understand the Child Argo CD Applications (FE & BE)

At this stage of the course, you already understand Argo CD Applications.

What is different now:

* These Applications are **not applied manually**
* They will be created by the **parent application**

### Sync options used in child applications

```yaml
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
      - ApplyOutOfSyncOnly=true
```

We use the following sync options:

* **CreateNamespace=true**
  Automatically creates the target namespace during sync

* **PruneLast=true**
  Applies new resources before removing obsolete ones

* **ApplyOutOfSyncOnly=true**
  Applies only resources that are out of sync

These options make the demo:

* Safer
* More predictable
* Easier to reason about

> Other sync options exist, but these are the most relevant at this stage.

### Critical point

We will **not apply** the frontend or backend Applications directly.

The **parent application** will be responsible for:

* Creating the child Applications
* Keeping them reconciled

---

## Step 4: Create Git Repositories

To keep authentication simple, we use **public GitHub repositories**.

Create the following repositories:

* `product1-be-config`
* `product1-fe-config`
* `product1-gitops`

Push contents accordingly:

| Repository         | Contents                                 |
| ------------------ | ---------------------------------------- |
| product1-be-config | Backend child app (Argo CD) + manifests  |
| product1-fe-config | Frontend child app (Argo CD) + manifests |
| product1-gitops    | Parent (App of Apps) application         |

### Why a separate `product1-gitops` repo?

* Represents the **product boundary**
* Owns the App of Apps definition
* Clearly separates product orchestration from component ownership

> **Note 1:** In this demo, we are using a design where the **child Argo CD Applications are stored in their respective tier or microservice config repositories**, while the **parent (App of Apps) Application is stored separately**.
>
> You may also encounter designs where **child Application YAMLs are stored alongside the parent Application** in the same repository. There is no universally correct or incorrect approach here — it is a **design choice**.
>
> The approach used in this demo helps **separate responsibilities**. For example, a senior DevOps or platform engineer may manage the **parent application and product-level orchestration**, while individual frontend, backend, or microservice teams (or junior DevOps engineers) manage their **respective child Applications and manifests**.

> **Note 2:** For this demo, we did **not create separate GitHub repositories for application source code and Dockerfiles**, even though you may see directories such as `product1-fe` and `product1-be` in the local directory structure.
>
> These directories are used only to **build container images locally for the demo** and are **not backed by dedicated GitHub repositories**. This is an intentional simplification to keep the focus on **Argo CD and the App of Apps pattern**.
>
> In real production setups, you will typically see **separate repositories for application source code**, **Dockerfiles**, and **GitOps configuration**. These repositories are usually connected through a **CI system** that builds images and updates GitOps manifests automatically.
>
> Since we are **not introducing a CI pipeline in this demo**, we have opted for a simpler approach with fewer moving parts.

---

## Step 5: Create and Apply the Parent Application (App of Apps)

This step is where the **App of Apps pattern comes to life**.

Here, we create a **parent Argo CD Application** that represents the **entire product**.
This application does not deploy frontend or backend workloads directly. Instead, its sole responsibility is to **discover, create, and manage the child Argo CD Applications** that make up the product.

### Parent Application Definition

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: product1-root
  namespace: argocd
spec:
  project: default

  sources:
    - repoURL: https://github.com/<your-github-username>/product1-fe-config.git
      targetRevision: main
      path: argo

    - repoURL: https://github.com/<your-github-username>/product1-be-config.git
      targetRevision: main
      path: argo

  destination:
    server: https://kubernetes.default.svc
    namespace: argocd

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

### What This Application Does

When this parent application is synced, Argo CD performs the following actions:

1. Clones each Git repository defined under `sources`
2. Reads the Argo CD Application manifests present in the `argo/` directories
3. Creates the **child Applications** (frontend and backend) in the Argo CD namespace
4. Continuously reconciles those child Applications to match the desired state defined in Git

At this point, Argo CD transitions from managing **individual Applications** to managing a **product composed of Applications**.

---

### Important Concepts Illustrated Here

* We are using the **same Argo CD Application CRD** that has been used throughout the course
* App of Apps does **not introduce a new resource type**
* It is purely a **usage pattern** built on top of existing Argo CD functionality

The use of `sources` demonstrates that a **single Application can pull definitions from multiple Git repositories**.
This is a feature of the Application CRD itself and can be used even outside of the App of Apps pattern.

---

### Why Multiple Sources Are Used

In this demo, each child Application (frontend and backend) is stored in its **own configuration repository**.

Using `sources` allows the parent application to:

* Reference **multiple repositories**
* Collect **multiple child Application definitions**
* Maintain clear ownership boundaries between tiers or services

This keeps product-level orchestration centralized, while allowing individual components to be managed independently.

---

### Why No `syncOptions` Are Defined Here

You may notice that `syncOptions` are **not** specified for the parent application.

This is intentional.

The parent application:

* Does **not deploy Kubernetes workloads**
* Does **not create namespaces**
* Does **not apply manifests such as Deployments or Services**

Its job is limited to managing **Argo CD Application resources**, which are lightweight control-plane objects.

Sync options such as `CreateNamespace`, `PruneLast`, or `ApplyOutOfSyncOnly` are meaningful when deploying workloads and are therefore defined in the **child Applications**, not in the parent.

---

### Apply the Parent Application

Apply the parent application manifest:

```bash
kubectl apply -f product1-root.yaml
```

Once applied, switch to the Argo CD UI and observe:

* The parent application (`product1-root`)
* The automatically created child Applications
* The cascading sync from parent → child → Kubernetes resources

This completes the transition from **application-level GitOps** to **product-level GitOps**.

---

## Step 6: Observe Behavior in the Argo CD UI

At this stage, the App of Apps hierarchy becomes visible in the Argo CD UI.

```
Parent Application
  └── Child Applications
        └── Kubernetes Resources
```

### What Happens During Sync

When the parent application is synced:

1. The **parent application** reconciles its defined sources
2. **Child Applications** (frontend and backend) are created automatically
3. Each child application syncs its own Git repository
4. Kubernetes resources are deployed to the target namespace

This flow demonstrates how control moves from **product-level orchestration** to **component-level deployment**.

### Benefits of This Approach

* Single entry point for managing the entire product
* Clean and organized Argo CD UI
* Clear product-level health visibility
* Simplified cluster bootstrapping
* Strong ownership and responsibility boundaries

---

## Step 7: Access the Application

To access the deployed product, port-forward the frontend service:

```bash
kubectl port-forward -n product1-ns svc/fe-svc 8081:80
```

Open the application in your browser:

```
http://localhost:8081
```

You should see:

* A response from the frontend service
* A backend API response embedded within the frontend output

This confirms that both tiers are deployed and communicating correctly.

---

## Step 8: Deletion and Self-Healing Behavior

The parent application has **automated sync**, **pruning**, and **self-healing** enabled.

Manually delete a child application:

```bash
kubectl delete applications.argoproj.io product1-fe -n argocd
```

Recheck the application state:

```bash
kubectl get applications -n argocd
```

You will observe that all applications are recreated and healthy:

```
product1-be     Synced   Healthy
product1-fe     Synced   Healthy
product1-root   Synced   Healthy
```

### Why This Happens

Argo CD continuously reconciles desired state from Git:

* Git remains the single source of truth
* The parent application detects drift
* The deleted child application is automatically recreated

This is GitOps **self-healing** in action.

---

## Conclusion

The App of Apps pattern provides a **clean and scalable way to manage products composed of multiple Argo CD Applications**.

Instead of treating frontend, backend, and other components as isolated units, App of Apps introduces a **product-level abstraction** using a parent Argo CD Application. This parent Application becomes the single entry point for orchestrating, observing, and reconciling the entire product.

Through this lecture and demo, you have seen how:

* A parent Application manages **other Applications**
* Child Applications retain full ownership of **Kubernetes workloads**
* Git becomes the source of truth not only for workloads, but also for **product composition**
* Argo CD continuously enforces desired state through sync, prune, and self-healing

While App of Apps is not mandatory for small setups, adopting it early helps establish a **clean GitOps model** that scales naturally as products grow in complexity, environments, and team ownership.

This pattern is foundational for operating Kubernetes platforms at scale and is widely used in real production environments.

---

## References

* **Argo CD Official Documentation – Application CRD**
  [https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)

* **Argo CD – App of Apps Pattern**
  [https://argo-cd.readthedocs.io/en/stable/operator-manual/app-of-apps/](https://argo-cd.readthedocs.io/en/stable/operator-manual/app-of-apps/)

* **Argo CD GitHub Repository**
  [https://github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)

* **CloudWithVarJosh – Argo CD: Basics to Production**
  [https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production](https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production)

---

