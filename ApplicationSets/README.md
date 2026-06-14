# Argo CD ApplicationSets Explained | Scaling GitOps Across Clusters & Microservices

## Video reference for this lecture is the following:

[![Watch the video](https://img.youtube.com/vi/FS__bq6I4m0/maxresdefault.jpg)](https://www.youtube.com/watch?v=FS__bq6I4m0&ab_channel=CloudWithVarJosh)


---
## ⭐ Support the Project  
If this **repository** helps you, give it a ⭐ to show your support and help others discover it! 

---


## Table of Contents

- [Introduction](#introduction)  
- [Why ApplicationSets?](#why-applicationsets)  
- [What is Multi-Cluster in Kubernetes?](#what-is-multi-cluster-in-kubernetes)  
- [Why Plain Argo CD Applications Do Not Scale](#why-plain-argo-cd-applications-do-not-scale)  
- [What are ApplicationSets?](#what-are-applicationsets)  
- [Responsibilities of ApplicationSets](#responsibilities-of-applicationsets)  
- [Demo 1: Multi-Region Application Deployment Using Argo CD ApplicationSets](#demo-1-multi-region-application-deployment-using-argo-cd-applicationsets)  
  - [Step 1: Create Amazon EKS Clusters in Multiple Regions](#step-1-create-amazon-eks-clusters-in-multiple-regions)  
  - [Step 2: Install and Prepare Argo CD in the Mumbai Cluster](#step-2-install-and-prepare-argo-cd-in-the-mumbai-cluster)  
  - [Step 3: Onboard the N. Virginia Cluster into Argo CD](#step-3-onboard-the-n-virginia-cluster-into-argo-cd)  
  - [Step 4: Create the Git Repository and Application Structure](#step-4-create-the-git-repository-and-application-structure)  
  - [Step 5: Understanding and Applying ApplicationSet YAML](#step-5-understanding-and-applying-applicationset-yaml)  
- [Other Generator Types](#other-generator-types)  
  - [Cluster Generator (Demo 2)](#1-cluster-generator-demo-2)  
  - [Git Generator (Directories) (Demo 3)](#2-git-generator-directories-demo-3)  
  - [Git Generator (Files) (Demo 4)](#3-git-generator-files-demo-4)  
  - [Matrix Generator (Demo 5)](#4-matrix-generator-demo-5)  
- [Choosing the Right ApplicationSet Generator](#choosing-the-right-applicationset-generator)  
- [Other ApplicationSet Generators (for completeness)](#other-applicationset-generators-for-completeness)  
- [Conclusion](#conclusion)  
- [References](#references)   

---

## Why ApplicationSets?

To understand why ApplicationSets exist, we must first understand **multi-cluster Kubernetes** and the operational pressure it creates on GitOps.

---

## What is Multi-Cluster in Kubernetes?

![Alt text](/images/10a.png)

Multi-cluster is a **generic term** that simply means operating more than one Kubernetes cluster.
However, in this context, multi-cluster refers specifically to **multiple Kubernetes clusters that are logically related and managed together**.

These clusters are independent from an infrastructure perspective, but they are connected by a **shared operational intent**. For example, the same application may be deployed across clusters for environment separation, high availability, or disaster recovery.

Each cluster still has its own control plane, nodes, networking, and lifecycle.

Multi-cluster here is **not about unrelated or isolated clusters** that have no operational relationship with each other. It is about **coordinating deployments and configurations across a defined set of clusters** in a consistent and repeatable way.

#### Why teams adopt multi-cluster

* **Failure Domain Isolation**
  A single cluster represents a shared blast radius. Control plane failures, misconfigurations, or cluster-level issues can affect all workloads at once. Multiple clusters isolate failures and improve overall system resilience.

* **Environment Separation**
  Development, staging, and production environments are commonly isolated into separate clusters. This provides stronger security boundaries, clearer operational ownership, and safer promotion of changes across environments. In addition to application workloads, each cluster also requires a standard set of platform components such as ingress controllers, monitoring, logging, and security tooling.

* **Geographic and Latency Requirements**
  Applications serving users across regions often run workloads closer to users. Deploying the same application in multiple clusters improves latency and availability without coupling regions operationally.

* **Compliance and Regulatory Needs**
  Certain workloads must run in specific regions or controlled environments. Multi-cluster architectures make it possible to satisfy regulatory constraints while keeping deployment models consistent.

As organizations grow, new clusters are added regularly to support scale, isolation, or regional expansion. These clusters must be brought online quickly with a predictable baseline of applications and platform services, without relying on manual configuration.

---


## Why Plain Argo CD Applications Do Not Scale

![Alt text](/images/10b.png)

At this stage, GitOps complexity increases significantly.

#### Operational challenges without ApplicationSets

* **Argo CD Application YAML Explosion**
  In multi-environment or multi-cluster setups, the same *application workload* needs to be deployed repeatedly with only minor differences such as cluster destination, namespace, or values files. Without ApplicationSets, each deployment requires a separate **Argo CD Application** manifest, leading to duplicated YAML and increased maintenance effort.

* **Manual Multi-Cluster Wiring**
  Argo CD supports multi-cluster deployments, but without ApplicationSets, each cluster must be explicitly wired using individual **Argo CD Application** definitions. Adding a new cluster often means copying existing YAML, modifying destinations, and manually validating changes. This approach does not scale and introduces human error.

* **Configuration Drift at Scale**
  When many **Argo CD Application** manifests are manually maintained, it becomes easy for configurations to diverge over time. Small changes applied to one **Argo CD Application** may not be consistently propagated, resulting in drift across clusters and environments, undermining the promise of GitOps.

* **Static GitOps in a Dynamic World**
  Real-world platforms are dynamic. Clusters are added or removed, environments evolve, and repository structures change. Plain **Argo CD Applications** and even the *App of Apps* pattern rely on static definitions and cannot react automatically to these changes without manual intervention.

ApplicationSets address these problems by making **Argo CD Application creation itself declarative, dynamic, and scalable**.

> ApplicationSets are not mandatory for GitOps, but they become valuable whenever GitOps must scale across **repeated deployment patterns**.

> **Note:** ApplicationSets are commonly used in multi-cluster and multi-environment setups, but their value is not limited to those scenarios.
> They are equally useful when managing **multiple similar Applications within a single cluster**, such as microservices, tenants, or environment variants.
> Their real strength appears wherever **deployment intent must be expressed once and applied repeatedly**, whether across clusters, environments, repositories, or services.

---

## What are ApplicationSets?

![Alt text](/images/10c.png)

An **ApplicationSet** is an Argo CD custom resource that defines **how Argo CD Applications should be created at scale**.

Instead of manually defining each **Argo CD Application**, an ApplicationSet describes:

* *where application definitions come from*
* *how they should be templated*
* *when they should be created or removed*

An ApplicationSet itself does **not deploy workloads**.
Its sole purpose is to **generate and manage Argo CD Applications declaratively**.

By taking responsibility for **Application creation itself**, ApplicationSets transform multi-cluster GitOps from a *manual and error-prone process* into a **declarative and scalable system**.

> ApplicationSets define **what Argo CD Applications should exist**, and Argo CD ensures they always do.


---

## Responsibilities of ApplicationSets

Once you understand what an ApplicationSet is, its responsibilities become clear.

#### How ApplicationSets work

* **Define Desired Argo CD Applications**
  ApplicationSets let you declare **which Argo CD Applications should exist**, rather than manually creating them one by one. This shifts GitOps from managing deployments to managing **application intent**.

* **Generate Argo CD Applications from Rules**
  An ApplicationSet uses generators to produce multiple parameter sets and combines them with a template. Each rendered output results in a concrete **Argo CD Application** resource.

* **Template Application Definitions**
  The template section looks similar to a standard Argo CD Application but supports variables. This allows the same application definition to be reused across clusters, environments, or regions with controlled variation.

* **Continuously Reconcile Application State**
  The ApplicationSet controller continuously evaluates generator inputs. When clusters are added, Git paths change, or entries are removed, the corresponding **Argo CD Applications are created, updated, or deleted automatically**.

* **Enable Scalable Multi-Cluster GitOps**
  By combining generators with templated destinations, ApplicationSets make it possible to manage many related clusters using a single declarative definition, without duplicating Application manifests.

---

## Demo 1: Multi-Region Application Deployment Using Argo CD ApplicationSets

---

## Demo Introduction

![Alt text](/images/10d.png)

In this demo, we will work with an application called **app1** that is accessed by users in **India** and the **United States**.

To meet real-world production requirements, app1 is deployed in **two AWS regions**:

* **Mumbai (ap-south-1)** – serves users in India
* **N. Virginia (us-east-1)** – serves users in the United States

The choice of these regions is driven by two key factors:

1. **Regulatory and Compliance Requirements**
   User data must remain within the geographic boundaries of its region.
   Data for Indian users should stay in India, and data for US users should stay in the United States.

2. **Latency and User Experience**
   Users are served from the region closest to them, ensuring lower latency and better application performance.

To manage this multi-region deployment, we will use **Argo CD ApplicationSets** and follow a **GitOps-driven approach**.

Instead of manually creating and managing separate Argo CD Applications for each region, we will define a **single ApplicationSet** that automatically generates and manages region-specific Applications.

While this demo uses a **single monolithic application (app1)** for simplicity, real-world production environments typically consist of:

* Multiple applications
* Tiered architectures
* Microservices-based designs

In such setups, the number of Kubernetes manifests and Argo CD Applications grows quickly, making manual management **error-prone and difficult to scale**.
ApplicationSets help address this challenge by centralizing intent and reducing operational overhead.

---

## Demo Prerequisites

Before proceeding, ensure the following tools and concepts are in place.

#### 1. AWS CLI, eksctl, and Helm

You must have the AWS CLI, eksctl, and Helm installed and configured.

Official documentation:

* AWS CLI: [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* eksctl: [https://eksctl.io/installation/](https://eksctl.io/installation/)
* Helm: [https://helm.sh/docs/intro/install/](https://helm.sh/docs/intro/install/)

---

#### 2. Kubernetes Contexts (Important)

In this demo, we will work with **two Amazon EKS clusters**, one in Mumbai and one in N. Virginia.
This requires frequent switching between Kubernetes contexts.

It is important that you **understand what a kubeconfig context is and how context switching works**, rather than just executing commands blindly.

To build this understanding, you can refer to the following resources from my CKA series:

* YouTube lecture:
  [https://www.youtube.com/watch?v=VBlI0IG4ReI&ab_channel=CloudWithVarJosh](https://www.youtube.com/watch?v=VBlI0IG4ReI&ab_channel=CloudWithVarJosh)

* GitHub notes:
  [https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2032](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2032)

---

#### 3. Helm

Helm is used during the Argo CD installation process.

You can follow the commands in this demo, but understanding **why Helm is used and what it does** will significantly improve your learning experience.

To learn Helm fundamentals, refer to the following lecture from my CKA course:

* YouTube lecture:
  [https://www.youtube.com/watch?v=yvV_ZUottOM&ab_channel=CloudWithVarJosh](https://www.youtube.com/watch?v=yvV_ZUottOM&ab_channel=CloudWithVarJosh)

* GitHub notes:
  [https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2043](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2043)

---

#### 4. Argo CD CLI

The Argo CD CLI is required to interact with Argo CD from the command line.

Official installation guide:

* [https://argo-cd.readthedocs.io/en/stable/cli_installation/](https://argo-cd.readthedocs.io/en/stable/cli_installation/)

---

>**Note**: All configuration files and manifests used in this demo are available in the **GitHub notes for this lecture**.
I strongly recommend that you **follow along step by step** and apply the changes yourself.
Hands-on practice is the best way to solidify ApplicationSet concepts and understand how GitOps works in real-world multi-region deployments.

---

## Step 1: Create Amazon EKS Clusters in Multiple Regions

For this demo, we will use **Amazon EKS** to simulate a realistic multi-region production environment.

The primary goal of this demo is to understand **how ApplicationSets manage multi-cluster GitOps**, not to design a production-grade EKS architecture.
For that reason, we intentionally use **simple and minimal EKS cluster configurations**.

If you are interested in more advanced EKS configurations, such as:

* production-grade networking
* multi-AZ high availability
* ingress and load balancer integrations
* stateful workloads on EKS

you can refer to the following resources:

* **eksctl configuration examples**:
  [https://github.com/eksctl-io/eksctl/tree/main/examples](https://github.com/eksctl-io/eksctl/tree/main/examples)

* **AWS Load Balancer Controller on EKS**:
  [https://github.com/CloudWithVarJosh/YouTube-Standalone-Lectures/tree/main/Lectures/03-ing-eks](https://github.com/CloudWithVarJosh/YouTube-Standalone-Lectures/tree/main/Lectures/03-ing-eks)

* **StatefulSets on Amazon EKS**:
  [https://github.com/CloudWithVarJosh/YouTube-Standalone-Lectures/tree/main/Lectures/02-STS-On-EKS](https://github.com/CloudWithVarJosh/YouTube-Standalone-Lectures/tree/main/Lectures/02-STS-On-EKS)

---

### Cluster Design for This Demo

We will create **two EKS clusters**, each in a different AWS region:

* **Mumbai (ap-south-1)**
  This cluster will:

  * serve users in India
  * run the **Argo CD control plane**, which requires additional capacity

* **N. Virginia (us-east-1)**
  This cluster will:

  * serve users in the United States
  * act purely as a workload cluster

For this reason, the Mumbai cluster has **more worker node capacity** compared to N. Virginia.

---

### EKS Configuration Files

All EKS configuration files are placed under the `01-eks/` directory.

---

#### 1. Mumbai Cluster Configuration

**File:** `01-eks/01-eks-config-mumbai.yaml`

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: cwvj-mumbai
  region: ap-south-1
  tags:
    project: applicationsets-demo
    region: mumbai

vpc:
  cidr: 10.10.0.0/16

managedNodeGroups:
  - name: cwvj-mumbai-ng
    instanceType: t3.small
    desiredCapacity: 2
```

Create the cluster using:

```bash
eksctl create cluster -f eks/01-eks-config-mumbai.yaml
```

---

#### 2. N. Virginia Cluster Configuration

**File:** `01-eks/02-eks-config-nvirginia.yaml`

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: cwvj-nvirginia
  region: us-east-1
  tags:
    project: applicationsets-demo
    region: nvirginia

vpc:
  cidr: 10.20.0.0/16

managedNodeGroups:
  - name: cwvj-nvirginia-ng
    instanceType: t3.small
    desiredCapacity: 1
```

Create the cluster using:

```bash
eksctl create cluster -f eks/02-eks-config-nvirginia.yaml
```

---

## Step 2: Install and Prepare Argo CD in the Mumbai Cluster

Before installing Argo CD, verify that your local machine can access **both EKS clusters**.

---

### Verify Kubernetes Contexts

* List all available Kubernetes contexts:

```bash
kubectl config get-contexts
```

You should see contexts corresponding to both clusters:

* `cwvj-mumbai`
* `cwvj-nvirginia`

To build this understanding of **Kubernetes context**, you can refer to the following resources from my CKA series:

* YouTube lecture: [mTLS , kubeconfig & Kubernetes Context](https://www.youtube.com/watch?v=VBlI0IG4ReI&ab_channel=CloudWithVarJosh)

* GitHub notes: [mTLS , kubeconfig & Kubernetes Context](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2032)

---

### Switch to the Mumbai Cluster Context

Argo CD will be installed **only in the Mumbai cluster**, which will act as the **GitOps control plane**.

* Switch context to the Mumbai cluster:

```bash
kubectl config use-context cwvj-mumbai
```

(Your context name may differ slightly depending on how eksctl configured it. Ensure the active context points to the Mumbai cluster.)

---

### Argo CD Installation Approach

We have already discussed Argo CD architecture and installation options in detail in **Lecture 2** of the *Argo CD: Basics to Production* series.

Reference:
[https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/02-Arch-Install#step-2-add-the-argo-cd-helm-repository](https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/02-Arch-Install#step-2-add-the-argo-cd-helm-repository)

To keep this demo focused on **ApplicationSets**, we will install Argo CD **quickly using Helm**.

---

### Install Argo CD Using Helm

**Reference:** https://argoproj.github.io/argo-helm/

```bash
# Add the official Argo CD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm

# Verify the repository is added
helm repo list

# Refresh Helm repository cache
helm repo update

# Search for Argo-related charts
helm search repo argo

# List available versions of the Argo CD Helm chart
helm search repo argo/argo-cd --versions
```

---

### Create Namespace and Install Argo CD

```bash
# Create argocd namespace
kubectl create namespace argocd

# Install Argo CD using Helm
# Note: At the time of recording this lecture, the latest Argo CD Helm chart version is 9.4.0.
# In production environments, systems typically run n-1 or n-2 versions for stability and predictability,
# rather than immediately adopting the latest (n) release.
helm install my-argo-cd argo/argo-cd --version 9.4.0 -n argocd

```

---

### Verify Argo CD Pods

```bash
# Verify Argo CD pods are running
kubectl get pods -n argocd
```

Proceed only once all pods are in `Running` state.

---

### Access Argo CD UI Using Port Forwarding

To access Argo CD locally:

```bash
# Port-forward Argo CD server to local machine
kubectl port-forward service/my-argo-cd-argocd-server -n argocd 8080:443
```

This command:

* Binds port `8080` on your local machine
* Tunnels traffic to the Argo CD server service inside the cluster
* Uses your kubeconfig and kubectl process

---

### Retrieve Argo CD Admin Password

```bash
# Retrieve Argo CD initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
-o jsonpath="{.data.password}" | base64 -d
```

---

### Login to Argo CD

```bash
# Open your browser and access
http://localhost:8080
```

* Login credentials:

  * Username: `admin`
  * Password: value retrieved from the previous command

---

### Update Admin Password

* Navigate to **User Info**
* Click **Update Password**
* Set a password of your choice

This completes the Argo CD setup.

---


## Step 3: Onboard the N. Virginia Cluster into Argo CD

At this stage, we have two EKS clusters up and running:

* Mumbai (ap-south-1)
* N. Virginia (us-east-1)

Argo CD is installed in the **Mumbai cluster**, and the Argo CD UI is accessible locally.
However, Argo CD currently knows only about the cluster it is running in. If Argo CD has no information about the N. Virginia cluster, it has no way to deploy or manage workloads there.

In this step, we will **register the N. Virginia cluster with Argo CD**, enabling true multi-cluster GitOps.

---

### Login to Argo CD

Before interacting with Argo CD, log in using the CLI.

```bash
# Login to Argo CD using local port-forwarded endpoint
argocd login localhost:8080
```

---

### Verify Clusters Known to Argo CD

Once logged in, list the clusters currently registered with Argo CD.

```bash
# List clusters registered with Argo CD
argocd cluster list
```

At this point, you should see **only one cluster**:

* `in-cluster`, which represents the Mumbai cluster where Argo CD is installed.

You can also verify this from the UI by navigating to:
**Settings → Clusters**
You should see only a single cluster listed.

---


### Add the N. Virginia Cluster

Add the N. Virginia cluster to Argo CD using the **kubeconfig context** available on your local machine.

It is important to understand that **`argocd cluster add` operates on kubeconfig contexts, not cluster names**.

List the available kubeconfig contexts:

```bash
kubectl config get-contexts
```

Example output:

```text
CURRENT   NAME                                             CLUSTER                              AUTHINFO
*         varun.joshi@cwvj-mumbai.ap-south-1.eksctl.io     cwvj-mumbai.ap-south-1.eksctl.io     varun.joshi@cwvj-mumbai.ap-south-1.eksctl.io
          varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io   cwvj-nvirginia.us-east-1.eksctl.io   varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io
```

The **NAME column** represents the kubeconfig **context** and is the value passed to `argocd cluster add`.

---

> **Important**
> All commands in this step run from your **thin client** (your laptop).
> During onboarding, the Argo CD **CLI** uses your **local kubeconfig and network** to access the target cluster.
> The Argo CD control plane (running in Mumbai) does **not** directly communicate with the N. Virginia cluster at this stage.

---

Add the N. Virginia cluster using the correct context:

```bash
argocd cluster add varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io
```

---

> **How this works**
> The `argocd cluster add` command:
>
> * reads authentication details from your local kubeconfig
> * connects to the N. Virginia cluster **from your laptop**
> * creates the required ServiceAccount and RBAC resources
> * securely stores cluster credentials in Argo CD as a Kubernetes Secret
>
> In production environments, cluster onboarding is often performed using restricted IAM roles or dedicated identities.
> For this demo, kubeconfig-based onboarding keeps the focus on **multi-cluster GitOps and ApplicationSets**, rather than access management.

---

### What happens next

Once onboarding is complete:

* the N. Virginia cluster appears in **Settings → Clusters**
* Argo CD can deploy and manage Applications on that cluster
* subsequent communication occurs **directly between the Argo CD control plane and the cluster API**

---

### Verify Cluster Registration

Verify that both clusters are now registered with Argo CD:

```bash
# Verify all clusters registered with Argo CD
argocd cluster list
```

You should see two entries:

* `in-cluster` (Mumbai)
* `varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io` (N. Virginia)

You can also confirm this from the Argo CD UI under:
**Settings → Clusters**


---

## Step 4: Create the Git Repository and Application Structure

To keep this demo focused on **ApplicationSets**, we will use a **public GitHub repository**.

If you are working with **private repositories**, authentication and access management are covered separately in **Lecture 04**:
[https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/04-PrivateRepo%2BSyncPruneSelfHeal](https://github.com/CloudWithVarJosh/ArgoCD-Basics-To-Production/tree/main/04-PrivateRepo%2BSyncPruneSelfHeal)

All files required for this demo are already available in the **GitHub notes for this lecture**.
I strongly recommend following along and performing the demo yourself; **GitOps is best learned by doing, not watching**.

---

#### Create the application configuration repository

Create a new Git repository named:

```
app1-config
```

This repository represents the **desired state** for the application across multiple regions.

---

#### Repository structure

At the root of the repository, create **two directories**, one for each region:

```
app1-config/
├── mumbai/
│   └── manifests/
│       ├── 01-cm.yaml
│       ├── 02-svc.yaml
│       └── 03-deploy.yaml
└── nvirginia/
    └── manifests/
        ├── 01-cm.yaml
        ├── 02-svc.yaml
        └── 03-deploy.yaml
```

Each `manifests/` directory contains the **complete Kubernetes manifests** required to deploy the application into that region.

---

## Step 5: Understanding and Applying ApplicationSet YAML (Generators and Templates)

In this step, we will **deeply understand what an ApplicationSet is**, how it works internally, and how it creates Argo CD Applications.

We will use the following **ApplicationSet manifest** throughout this step to understand:

* the overall syntax of an ApplicationSet
* the role of **generators**
* the role of **templates**
* how inputs flow from generators into templates

---

## What is an ApplicationSet (Conceptual Understanding)

In simple terms, an **ApplicationSet** is a Kubernetes **custom resource** that **creates Argo CD Applications**.

To understand this better, let’s draw a parallel with something we already know well.

* A **Deployment** creates **Pods**
* A **Deployment manifest** has:

  * metadata and spec describing the Deployment itself
  * a **template** section describing the Pods it will create

Similarly:

* An **ApplicationSet** creates **Argo CD Applications**
* An **ApplicationSet manifest** has:

  * fields that describe *how many Applications should be created and for whom*
  * a **template** section that describes the Argo CD Applications that will be generated

> Just like a Deployment never directly creates containers but creates Pods from a template,
> an ApplicationSet never deploys workloads directly but creates Argo CD Applications from a template.

The **template section of an ApplicationSet is nothing but a standard Argo CD Application YAML**, which we have been working with throughout this course.

---

## ApplicationSet Manifest Used in This Demo

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app1-multi-region
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error

  generators:
  - list:
      elements:
      - region: mumbai
        destinationName: in-cluster
        namespace: app1-mumbai-ns
      - region: nvirginia
        destinationName: varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io
        namespace: app1-nvirginia-ns

  template:
    metadata:
      name: "app1-{{.region}}"
    spec:
      project: default

      source:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        targetRevision: main
        path: "{{.region}}/manifests"

      destination:
        name: "{{.destinationName}}"
        namespace: "{{.namespace}}"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

We will now break this manifest down piece by piece.

---

## Core Building Blocks of an ApplicationSet

An ApplicationSet has **two fundamental building blocks**:

1. **Generators**
2. **Template**

---

## 1) Generators

Generators define the **scope of the ApplicationSet**.

They answer very important questions:

* How many Applications need to be created?
* For which targets?
* Based on what source of truth?

Generators **do not define application behavior**.
They do **not** talk about:

* Git repositories
* sync policies
* namespaces
* or how an app behaves

Their only responsibility is to define **where and for whom Applications should exist**.

---

### List Generator (Used in This Demo)

In this demo, we are using the **list generator**, which is the most explicit and beginner-friendly generator.

```yaml
generators:
- list:
    elements:
    - region: mumbai
      destinationName: in-cluster
      namespace: app1-mumbai-ns
    - region: nvirginia
      destinationName: varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io
      namespace: app1-nvirginia-ns
```

Think of each **element in the list as one deployment target**.

In our demo:

* We have **two regions**
* We have **two Kubernetes clusters**
* We want **two Argo CD Applications**

That is why we have **two elements** in the list.

Each element captures:

* the region context
* the destination cluster identity
* the namespace where the app should be deployed

You should form a mental picture here:

> We are dealing with multiple Kubernetes clusters.
> Each cluster has its own identity and namespaces.
> These differences must be modeled somewhere, and that “somewhere” is the generator.

All values defined in the generator become **inputs** that the template later consumes.

> **Note**
> In this demo, we are intentionally using the **list generator** because it is explicit and easy to follow.
> ApplicationSets support several other generator types (such as cluster, git, and matrix generators), which are better suited for larger and more dynamic platforms.
> To avoid breaking the flow of the demo, we will continue using the list generator here and discuss other generator types **after the demo is complete**.
---

## 2) Template

The **template** is nothing more than a **blueprint for an Argo CD Application**.

This section defines:

* what the Application should look like
* where it pulls manifests from
* how it syncs
* where it deploys

The most important thing to understand is:

> The template section is evaluated **once per generator element**.

Since our list generator has **two elements**, this template is rendered **twice**, resulting in **two Argo CD Applications**.

---

### Template Metadata

```yaml
metadata:
  name: "app1-{{.region}}"
```

Here:

* `{{.region}}` comes from the generator
* For Mumbai, this becomes `app1-mumbai`
* For N. Virginia, this becomes `app1-nvirginia`

This is how **unique Application names** are generated automatically.

---

### Source Section

```yaml
source:
  repoURL: https://github.com/CloudWithVarJosh/app1-config.git
  targetRevision: main
  path: "{{.region}}/manifests"
```

This tells Argo CD:

* which repository to pull manifests from
* which branch to use
* which folder inside the repo to deploy

Because the repository is structured by region:

* `mumbai/manifests`
* `nvirginia/manifests`

the `{{.region}}` variable dynamically selects the correct manifests per Application.

---

### Destination Section

```yaml
destination:
  name: "{{.destinationName}}"
  namespace: "{{.namespace}}"
```

This defines **where workloads are deployed**.

* Mumbai uses `in-cluster` because Argo CD runs there
* N. Virginia uses its registered external cluster name

This distinction is critical:

> The cluster where Argo CD runs is always referenced as `in-cluster`.
> All other clusters must be explicitly referenced by their registered name.

---

### Sync Policy

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

This enables standard GitOps behavior:

* unmanaged resources are pruned
* drift is auto-corrected
* namespaces are created automatically if missing

Each generated Application gets its **own independent sync policy**.

---

### Understanding `goTemplate` and `goTemplateOptions`

```yaml
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error
```

Enabling `goTemplate` allows us to use **Go templating**, which is more powerful and strict than basic variable substitution.

If you are already familiar with **Helm**, this syntax will look familiar.
Helm charts also use **Go templates**, which is why you see the same `{{ }}` notation there.

Go is a general-purpose programming language, and Go templating gives us access to:

* variable interpolation
* conditionals and functions
* stricter error handling

ApplicationSets leverage Go templates to make multi-cluster and multi-environment definitions expressive and safe.

The option:

```yaml
missingkey=error
```

forces ApplicationSet rendering to **fail fast** when:

* a variable is referenced in the template
* but not provided by the generator

Without this option, missing values may silently render as empty strings, leading to hard-to-detect misconfigurations.
For this reason, enabling `missingkey=error` is considered a **best practice**, especially in production setups.

---

## Summary: How Generators and Templates Work Together

* **Generators define all the inputs**
* **Templates define the Argo CD Application blueprint**
* The ApplicationSet controller:

  * iterates over generator elements
  * injects values into the template
  * creates one Argo CD Application per element

At this point, you should have a clear mental model of **how a single ApplicationSet can reliably manage multiple Applications across clusters and regions**.

---

## Apply the ApplicationSet Manifest

Now that we understand the YAML, let’s apply it.

```bash
# Apply the ApplicationSet manifest
kubectl apply -f app1-ApplicationSet.yaml

# Verify ApplicationSet creation
kubectl get applicationset -n argocd
```

---

## Observation

At this point:

* Open the Argo CD UI at **[http://localhost:8080](http://localhost:8080)**
* Navigate to **Applications**

You will observe that:

* **Two Argo CD Applications are created automatically**
* Their status is **not green**

This is expected.

The Applications are created as soon as the ApplicationSet is applied, but they cannot sync yet because **the Git repository content has not been created or pushed**.

The important takeaway here is:

> Applications were created automatically **because the ApplicationSet was created**.

This completes the understanding phase.

---

# Other Generator Types

So far, we have used the **list generator** to deploy `app1` to:

* Mumbai (in-cluster)
* N. Virginia (external cluster)

The reason this worked well is because the list generator is **explicit**.
We directly told ApplicationSet:

> create two Applications, one for each region and cluster.

Now let’s understand **how we could achieve similar outcomes using other generators**, and why teams might choose them.

**Reference:** https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/

---


## 1. Cluster Generator (Demo 2)

The **cluster generator** creates Argo CD Applications by iterating over **Kubernetes clusters already registered in Argo CD**.

Clusters are selected using **labels**, and **one Application is generated per matching cluster**.

In this model:

* **Argo CD’s cluster inventory** is the source of truth
* Cluster labels drive Application generation
* Applications automatically appear or disappear as clusters are added, labeled, or removed

The cluster generator is best suited for **infrastructure-driven GitOps**, where applications are expected to **follow clusters** across regions, environments, or platforms.

---

Below is a **complete ApplicationSet YAML** using the **cluster generator**.
This achieves the same intent as our list generator based demo, but in a more dynamic, infrastructure-driven way.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app1-cluster-generator
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error

  generators:
    - clusters:
        selector:
          matchLabels:
            app: app1

  template:
    metadata:
      name: "app1-{{.metadata.labels.region}}"
    spec:
      project: default

      source:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        targetRevision: main
        path: "{{.metadata.labels.region}}/manifests"

      destination:
        name: "{{.name}}"
        namespace: "app1-{{.metadata.labels.region}}-ns"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

---

### What this YAML is doing

The **cluster generator** creates Argo CD Applications by iterating over **Kubernetes clusters already registered in Argo CD**.

Argo CD evaluates its internal **cluster inventory** and selects clusters based on **labels** defined on those clusters.

For each cluster that matches the selector, the ApplicationSet controller generates **one Argo CD Application** using the shared template.

---

### How this maps to our demo

In our demo, we manually defined deployment targets using the list generator:

* Mumbai → `in-cluster`
* N. Virginia → external cluster

With the cluster generator, we express intent differently:

> Deploy `app1` to **all clusters that belong to this platform**.

The actual cluster identities are discovered dynamically by Argo CD at runtime, instead of being hard-coded in Git.

---

### Prerequisite: labeling clusters in Argo CD

Clusters **must be labeled inside Argo CD**, because labels are what the cluster generator uses as its input.

For **external clusters**, labels are typically added at onboarding time using the CLI:

```bash
argocd cluster add <context> --label app=app1 --label region=nvirginia --upsert
```

> **Note**: The `--upsert` flag is required when the cluster is already registered with Argo CD.  
> It instructs Argo CD to **update the existing cluster metadata (labels)** instead of failing due to a spec mismatch.


This registers the cluster with Argo CD and persists the labels as part of Argo CD’s internal cluster inventory.

---

For the **in-cluster** (the cluster where Argo CD itself is running), the situation is slightly different.

The in-cluster is **implicitly registered** when Argo CD is installed and therefore is **not normally added using `argocd cluster add`**.
Instead, labels are typically applied **after installation**.

The most common and recommended approach is via the Argo CD UI:

> **Settings → Clusters → in-cluster → Edit → Add Labels**

This updates the metadata associated with the in-cluster entry that the ApplicationSet controller reads.

> **Note**
> It is also possible to label the in-cluster via the CLI by modifying Argo CD’s internal cluster inventory (which ultimately backs onto Kubernetes objects managed by Argo CD).
> However, for clarity and safety, the UI approach is preferred when working with the in-cluster, especially in demos and learning environments.

Once applied, these labels are available to both the **cluster generator** and the **ApplicationSet template**, exactly the same way as labels on external clusters.

From the perspective of the ApplicationSet controller, there is **no distinction** between in-cluster and external clusters; both are treated as entries in Argo CD’s cluster inventory.

---

### Understanding the generator section

```yaml
generators:
- clusters:
    selector:
      matchLabels:
        app: app1
```

This tells the ApplicationSet controller:

> Create one Application for **every cluster labeled `app=app1`**.

Any cluster added later with the same label automatically receives an Application, without modifying Git or the ApplicationSet YAML.

---

### How variables like `{{.name}}` are resolved

When using the **cluster generator**, Argo CD exposes a predefined cluster object to the template, including:

* `name` – the cluster name as known to Argo CD
* `server` – the Kubernetes API server address
* `metadata.labels` – cluster labels
* `metadata.annotations` – cluster annotations

This is why variables like `{{.name}}` and `{{.metadata.labels.region}}` work without being explicitly defined in the generator.

---

### Understanding the template and production-friendly naming

```yaml
metadata:
  name: "app1-{{.metadata.labels.region}}"
```

Although `{{.name}}` is available, using it directly for Application naming is usually **not ideal**, because cluster names are often long and implementation-specific.

Instead, we use a **business-level identifier**, such as `region`, derived from cluster labels.

This results in predictable, readable Application names like:

* `app1-mumbai`
* `app1-nvirginia`

---

### Source and destination explained

```yaml
source:
  repoURL: https://github.com/CloudWithVarJosh/app1-config.git
  targetRevision: main
  path: "{{.metadata.labels.region}}/manifests"
```

The Git repository is structured by region, so the label dynamically selects the correct manifest directory.

```yaml
destination:
  name: "{{.name}}"
  namespace: "app1-{{.metadata.labels.region}}-ns"
```

Here:

* `destination.name` uses the actual Argo CD cluster identity
* The Application is deployed to the correct cluster automatically

This cleanly separates **technical identity** from **human-readable intent**.

---

### Note: verifying `{{.metadata.labels.region}}`

The value used by `{{.metadata.labels.region}}` can be **cross-checked directly from the cluster-specific Secret** maintained by Argo CD.

First, list all cluster secrets:

```bash
kubectl get secrets -n argocd
```

You will see entries similar to:

```text
cluster-9e43b85016537c5b4557806b2f581817.sk1.us-east-1.eks.amazonaws.com-499980605
cluster-kubernetes.default.svc-3396314289
```

Each of these represents a cluster registered with Argo CD.

To verify labels for the in-cluster, inspect its Secret:

```bash
kubectl get secret -n argocd cluster-kubernetes.default.svc-3396314289 -o yaml
```

The following section is what the ApplicationSet template reads:

```yaml
metadata:
  labels:
    app: app1
    region: mumbai
```

This mapping directly explains why the template expression
`{{.metadata.labels.region}}` resolves correctly.

---

### What happens and when teams use this pattern

* One Application is created per matching cluster
* New clusters are picked up automatically
* Removing a cluster removes the corresponding Application
* Cluster lifecycle directly drives Application lifecycle

This pattern is commonly used in:

* large platforms with many clusters
* environments where clusters are frequently created or destroyed
* operational models where applications are expected to “follow clusters”


>**Key takeaway** The cluster generator is **infrastructure-driven GitOps**.
> Argo CD discovers clusters automatically via its internal inventory, while you retain full control over how Applications are named and structured.

This keeps Git clean, scalable, and aligned with real platform growth.


---


## 2. Git Generator (Directories) (Demo 3)

The **Git directory generator** creates Argo CD Applications by discovering **directories in a Git repository** and deploying the manifests contained within them.

Each matching directory represents a **deployment unit**, and **one Argo CD Application is generated per directory** using a shared template.

In this model:

* **Git folder structure** is the source of truth
* Application lifecycle is driven by directory creation or removal
* Adding or deleting a directory directly creates or deletes an Application

This design is **very common in real-world platforms**, especially when multiple environments such as `dev`, `staging`, and `prod` must be deployed **into the same Kubernetes cluster** in a consistent and repeatable way.

The Git directory generator is best suited for **structure-driven GitOps**, where teams want a **simple and intuitive mapping** between Git layout and deployed Applications, without coupling application definitions to cluster metadata.

---

Below is a **complete ApplicationSet YAML** using the **Git directory generator**.

This pattern deliberately shifts the source of truth from **infrastructure** to **Git structure**.

Instead of discovering clusters dynamically, the ApplicationSet controller scans a Git repository, interprets its directory layout, and generates Applications accordingly.

---

### Mapping to our demo

In this demo repository, the directory layout encodes **both region and environment intent** directly:

```
app1-config/
└── mumbai/
    ├── dev/
    │   └── manifests/
    ├── stage/
    │   └── manifests/
    └── prod/
        └── manifests/
```

Here:

* `mumbai` represents the **regional boundary**
* `dev`, `stage`, and `prod` represent **environments**

Each **environment directory under `mumbai/`** represents a distinct deployment of the same application into the same cluster.

This mirrors a **very common production GitOps layout**, where:

* region is encoded at a higher directory level
* environments are modeled as subdirectories
* deployments are isolated using namespaces

---

### Git directory generator YAML

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app1-git-directories
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error

  generators:
    - git:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        revision: main
        directories:
          - path: "mumbai/*"

  template:
    metadata:
      name: "app1-{{.path.basename}}"
    spec:
      project: default

      source:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        targetRevision: main
        path: "{{.path.path}}/manifests"

      destination:
        name: in-cluster
        namespace: "app1-{{.path.basename}}-ns"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

---

### What this YAML is doing

The **Git directory generator** performs the following steps:

* scans the specified Git repository and revision
* discovers directories matching `mumbai/*`
* identifies `mumbai/dev`, `mumbai/stage`, and `mumbai/prod`
* treats **each environment directory** as one deployment input
* renders one Argo CD Application per directory using the template

Here, **Git structure itself becomes the deployment contract**.

Each matched directory is assumed to represent a valid environment that contains a `manifests/` folder.

---


### How variables are resolved

For each directory discovered, the Git directory generator exposes a **`path` object** to the template when Go templating is enabled.

> The key point is that **`path` is an object, not a string**.

It contains structured information about the matched directory.

* `.path.path` – the **full relative directory path** that matched the glob
  (for example, `mumbai/dev`)
* `.path.basename` – the **leaf directory name only**
  (`dev`, `stage`, `prod`)

---

### What the `path` object actually looks like

For a matched directory such as `mumbai/dev`, Argo CD internally exposes:

```text
.path = {
  path:     "mumbai/dev",
  basename: "dev",
  segments: ["mumbai", "dev"]
}
```

So:

* `.path` ❌ → the entire object
* `.path.path` ✅ → string `"mumbai/dev"`
* `.path.basename` ✅ → string `"dev"`

This is why **`.path` alone cannot work**.

---

### Why `.path` alone cannot be rendered

It is natural to think of `.path` as:

```text
"path" = "mumbai/dev"
```

But Argo CD actually sees:

```text
"path" = { path: "...", basename: "...", segments: [...] }
```

So if you wrote:

```yaml
path: "{{.path}}/manifests"
```

Argo CD would attempt to stringify an **object**, resulting in either:

* a template render error, or
* confusing output such as
  `map[path:mumbai/dev basename:dev …]`

That is why Argo CD **forces you to be explicit** and select a specific field.

---

### How these values are used in practice

These fields are injected into the template and reused consistently across:

* Application name
* Git source path
* Namespace name

This distinction is intentional:

* `.path.path` is used when Argo CD needs to know **where to read manifests from** in Git
  (structural context: region + environment)
* `.path.basename` is used when Argo CD needs a **clean, human-readable identifier**
  (logical identity: environment only)

Because Go templating is enabled, all variables must be accessed explicitly via the `.path` object.
This avoids ambiguity, prevents silent misconfiguration, and aligns with the **official ApplicationSet documentation and examples**.

---


### Understanding the template and naming

```yaml
metadata:
  name: app1-{{.path.basename}}
```

This results in clean, predictable Application names:

* `mumbai/dev` → `app1-dev`
* `mumbai/stage` → `app1-stage`
* `mumbai/prod` → `app1-prod`

Even though the Git path includes the region, **the Application name intentionally does not**.
This keeps names short, stable, and readable.

---

### Source and destination explained

```yaml
source:
  path: "{{.path.path}}/manifests"
```

Each Application pulls manifests from its **full environment-specific path**, such as:

* `mumbai/dev/manifests`
* `mumbai/stage/manifests`
* `mumbai/prod/manifests`

```yaml
destination:
  name: in-cluster
  namespace: app1-{{.path.basename}}-ns
```

All Applications deploy to **the same Kubernetes cluster**, but to **separate namespaces**:

* `app1-dev-ns`
* `app1-stage-ns`
* `app1-prod-ns`

This is intentional and aligns with a **very common production pattern**:

> Multiple environments deployed into the same cluster, isolated by namespaces, and driven entirely by Git structure.

---

### Widening the imagination (production-grade)

In real-world setups, it is very common to have **multiple ApplicationSet YAMLs**, each scoped to a region or platform:

* One ApplicationSet deploying `dev`, `stage`, `prod` under **Mumbai**
* Another ApplicationSet deploying `dev`, `stage`, `prod` under **N. Virginia**

Each ApplicationSet still uses the **Git directory generator**, but targets a different cluster.

This keeps:

* YAML simple
* responsibility boundaries clear
* cluster logic out of application definitions

---

### What happens and when teams use this pattern

* One Application is created per environment directory
* Adding a directory creates a new Application
* Removing a directory removes the corresponding Application
* Git history clearly reflects environment evolution

This pattern is commonly used when:

* application teams own their Git structure
* environments are Git-defined
* platform teams want minimal coupling to cluster inventory
* simplicity and auditability are preferred over dynamic discovery

---

> **Key takeaway:**
> With the Git directory generator, **Git structure is the API**.
> It defines *what exists*, while cluster selection is handled separately.

---


## 3. Git Generator (Files) (Demo 4)

The **Git file generator** creates Argo CD Applications by reading **structured data from files stored in Git**.

Each entry in the file represents a **logical Application definition**, and **one Argo CD Application is generated per entry** using a shared template.

In this model:

* **Git configuration files** are the source of truth
* Application lifecycle is driven by changes to declared data
* Adding, modifying, or removing entries explicitly controls which Applications exist

Unlike the directory generator, intent here is **not inferred**.
It is **explicitly declared**.

The Git file generator is best suited for **data-driven and governance-focused GitOps**, where deployment intent must be **explicit, auditable, and centrally controlled**, and where folder structure alone is insufficient or undesirable.

---

Below is a **complete ApplicationSet YAML** using the **Git file generator**.

This pattern treats Git as a **configuration database**, rather than a directory layout.

Instead of discovering intent from folders, we **declare it explicitly in a file**.

---

### Repository structure (production-style)

A very common and recommended layout is to store deployment metadata under a dedicated configuration file, separate from application manifests.

```
app1-config/
├── clusters.yaml
├── mumbai/
│   └── manifests/
└── nvirginia/
    └── manifests/
```

This cleanly separates:

* **what to deploy** (Kubernetes manifests)
* **where to deploy** (configuration data)

The `clusters.yaml` file is fully **version-controlled**, reviewed via pull requests, and audited like any other production configuration.

---

### Mapping to a production-style demo

In many real platforms, application deployment configuration is **centralized** and owned by a platform or SRE team.

Instead of allowing teams to infer intent from directory structures, the platform defines a file such as:

```yaml
# clusters.yaml
- name: app1-mumbai
  region: mumbai
  cluster: in-cluster
  namespace: app1-mumbai-ns

- name: app1-nvirginia
  region: nvirginia
  cluster: varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io
  namespace: app1-nvirginia-ns
```

Each list entry represents **one desired Application**.

This file becomes the **single source of truth** for where and how the application is deployed.

---

### Git file generator YAML (Go templating enabled)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app1-git-files
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error

  generators:
    - git:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        revision: main
        files:
          - path: clusters.yaml

  template:
    metadata:
      name: "{{.name}}"
    spec:
      project: default

      source:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        targetRevision: main
        path: "{{.region}}/manifests"

      destination:
        name: "{{.cluster}}"
        namespace: "{{.namespace}}"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

---

### How variables are resolved

With the Git file generator, **each YAML entry is exposed directly to the template as a structured object**.

For the following entry in `clusters.yaml`:

```yaml
- name: app1-mumbai
  region: mumbai
  cluster: in-cluster
  namespace: app1-mumbai-ns
```

Argo CD exposes the values as top-level fields when Go templating is enabled:

* `{{.name}}`
* `{{.region}}`
* `{{.cluster}}`
* `{{.namespace}}`

Unlike the Git directory generator, there is **no derived `path` object**, because the data is already explicitly declared.

Each field maps **directly** to a key in the YAML file, making the template simple, readable, and deterministic.

Enabling `missingkey=error` ensures the ApplicationSet **fails fast** if any required field is missing, which is critical in governance-focused environments.

---

### What this YAML is doing

The **Git file generator**:

* reads structured data from a Git-tracked file
* treats each list entry as one desired Application
* injects those values directly into the Application template
* creates exactly one Argo CD Application per entry

Here, Git is no longer just storing manifests.
It is storing **deployment intent as data**.

---

### Why teams use this pattern in production

This pattern is commonly used when:

* deployment targets must be **explicitly approved**
* environments or regions cannot be inferred from directory structures
* platform teams own cluster access
* auditability and compliance matter more than flexibility

Typical real-world examples:

* regulated industries (finance, healthcare)
* large enterprises with central platform teams
* shared clusters with strict namespace controls
* environments where clusters appear and disappear independently of application code

---

### How this differs from the directory generator

| Generator     | Source of truth             |
| ------------- | --------------------------- |
| Git directory | Folder structure            |
| Git file      | Explicit configuration data |

With the directory generator:

* structure implies intent

With the file generator:

* intent is declared, reviewed, and enforced

---

> **Key takeaway:** With the Git file generator, **Git becomes a configuration database**.
> The ApplicationSet template turns **declared data into Applications**.

This model intentionally trades flexibility for **clarity, control, and governance**, which is why it is widely adopted in mature, production-grade platforms.

---

### Generator selection recap (tie-back)

* **Cluster generator** → infrastructure-driven GitOps
* **Git directory generator** → structure-driven GitOps
* **Git file generator** → data-driven, governance-first GitOps

---

## 4. Matrix Generator (Demo 5)

The **matrix generator** creates Argo CD Applications by **combining multiple generators** and generating an Application for **every valid combination** of their outputs.

Each generator represents **one deployment dimension**, and the matrix generator computes the **Cartesian product** of those dimensions.

In this model:

* **Multiple sources of truth** define deployment intent
* Application lifecycle is driven by changes across all dimensions
* One Argo CD Application is created per valid combination

Unlike single generators, intent here is **composed**.
It is **derived by combining multiple independent inputs**.

The matrix generator is best suited for **multi-dimensional GitOps**, where applications must be deployed across **multiple clusters and environments** using a **single declarative definition**.

---

Below is a **complete ApplicationSet YAML** using the **matrix generator**.

This pattern allows GitOps to scale **without duplicating ApplicationSets** while keeping intent clear and explicit.

Instead of managing separate ApplicationSets per cluster or environment, we **combine generators** to express deployment intent in one place.

---

### Repository structure (production-style)

In this model, the Git repository encodes **environment only**.
Cluster and region are **not inferred from Git** and are instead defined explicitly.

```
app1-config/
├── dev/
│   └── manifests/
│       └── deploy.yaml
├── stage/
│   └── manifests/
│       └── deploy.yaml
└── prod/
    └── manifests/
        └── deploy.yaml
```

This layout intentionally separates concerns:

* **Environments** are defined by directory structure
* **Deployment targets (clusters/regions)** are defined outside Git structure

This is a very common and recommended design in real platforms.

---

### Mapping to a production-style demo

In this demo, we want to deploy:

* **One application**
* To **two Kubernetes clusters**

  * Mumbai cluster (`in-cluster`)
  * N. Virginia cluster
* Across **three environments**

  * dev
  * stage
  * prod
* Using **a single Git repository**

This results in **six Argo CD Applications**, all managed by **one ApplicationSet**.

---

### Matrix generator YAML (Go templating enabled)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app1-matrix-clusters
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error

  generators:
    - matrix:
        generators:
          # Dimension 1: environments from Git
          - git:
              repoURL: https://github.com/CloudWithVarJosh/app1-config.git
              revision: main
              directories:
                - path: "*"

          # Dimension 2: deployment targets (clusters)
          - list:
              elements:
                - region: mumbai
                  clusterName: in-cluster
                - region: nvirginia
                  clusterName: varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io

  template:
    metadata:
      name: "app1-{{.path.basename}}-{{.region}}"
    spec:
      project: default

      source:
        repoURL: https://github.com/CloudWithVarJosh/app1-config.git
        targetRevision: main
        path: "{{.path.basename}}/manifests"

      destination:
        name: "{{.clusterName}}"
        namespace: "app1-{{.path.basename}}-ns"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

---

### How variables are resolved

The matrix generator combines **outputs from both generators** and exposes a **merged parameter set** to the template.

### From the Git directory generator

For a directory such as `dev`, the generator exposes a `.path` object:

* `.path.path` → full matched directory path
  (`dev`)
* `.path.basename` → environment name
  (`dev`, `stage`, `prod`)

In this example, Git contributes **environment context only**.

---

### From the list generator

Each list element is exposed directly as template variables:

* `.region` → logical region identifier
  (`mumbai`, `nvirginia`)
* `.clusterName` → Argo CD cluster **NAME**
  (must exactly match `argocd cluster list`)

The list generator provides **deployment target metadata**, not inferred from Git.

---

### Combined view (important mental model)

For the `dev` directory and the `nvirginia` list entry, the resolved data looks like:

```
.path.basename = "dev"
.region        = "nvirginia"
.clusterName  = "varun.joshi@cwvj-nvirginia.us-east-1.eksctl.io"
```

These values are then injected into:

* Application name
* Git source path
* Destination cluster
* Namespace

Enabling `missingkey=error` ensures the ApplicationSet **fails fast** if any required value is missing, which is critical when combining generators.

---

### What this YAML is doing

The **matrix generator**:

* evaluates each generator independently
* computes the Cartesian product of their outputs
* injects the merged values into the template
* creates **one Argo CD Application per combination**

Given:

* 3 environments (dev, stage, prod)
* 2 clusters (mumbai, nvirginia)

The matrix produces **6 Applications**.

---

### Applications created

```
app1-dev-mumbai
app1-stage-mumbai
app1-prod-mumbai

app1-dev-nvirginia
app1-stage-nvirginia
app1-prod-nvirginia
```

All of them:

* Use the **same Git repo**
* Use the **same manifest structure**
* Deploy to **different clusters**
* Are uniquely and predictably named

---

### Why teams use this pattern in production

This pattern is commonly used when:

* applications must span **multiple clusters and environments**
* cluster topology should **not** be inferred from Git folders
* duplication of ApplicationSets must be avoided
* platform teams want **one authoritative deployment model**

It is especially common in **multi-cluster and platform-driven architectures**.

---


## Choosing the Right ApplicationSet Generator

By now, we have seen the following ApplicationSet generators:

**List, Cluster, Git (Directory), Git (Files), Matrix**

The key insight to internalize is not *how* these generators work, but **where deployment intent lives**.

> **There is no “best” generator.
> The correct generator is the one that matches the ownership and location of intent.**

ApplicationSet generators are **architectural primitives**.
Each one answers the same question in a different way:

> *Who decides that an Application should exist, and how is that decision expressed?*

Once you view generators through this lens, their purpose becomes obvious.

---

### Generator decision matrix

| Generator           | Where intent lives        | When it fits best                         | Primary strength           | Cost of choosing it      |
| ------------------- | ------------------------- | ----------------------------------------- | -------------------------- | ------------------------ |
| **List**            | Explicit YAML             | Small scale, deliberate control           | Predictable, reviewable    | Manual, does not scale   |
| **Cluster**         | Argo CD cluster inventory | App must follow clusters automatically    | Zero duplication           | Tightly coupled to infra |
| **Git (Directory)** | Git repository structure  | Environments are folder-defined           | Simple, intuitive          | Git layout becomes API   |
| **Git (Files)**     | Config data in Git        | Governance, approval, auditability matter | Explicit and controlled    | More configuration       |
| **Matrix**          | Multiple intent sources   | Scale across independent dimensions       | Compositional and scalable | Requires discipline      |

---

### Reading the table correctly

Do **not** read this table row by row.
Read it **column by column**.

* The **left side** describes *who owns intent*
* The **middle** describes *how intent is expressed*
* The **right side** describes *what you pay for that choice*

Every production GitOps platform makes **one or two of these choices**, never all of them.

---

### Architectural patterns you will see in practice

| Platform reality                      | Generator pattern                |
| ------------------------------------- | -------------------------------- |
| Few clusters, few environments        | **List**                         |
| Platform-owned clusters               | **Cluster**                      |
| App teams own environment lifecycle   | **Git (Directory)**              |
| Central SRE or governance model       | **Git (Files)**                  |
| Many clusters *and* many environments | **Matrix (composed generators)** |

---

### One critical clarification about Matrix

> **Matrix does not create intent.**

Matrix **only combines intent** that already exists elsewhere.

It is never used *instead of* another generator.
It is used **with** other generators when there are **multiple independent dimensions**, such as:

* environments × clusters
* regions × tenants
* apps × platforms

If there is only **one dimension**, Matrix is unnecessary and usually a smell.

---

### Practical rule of thumb

* **One source of intent** → one generator
* **More than one independent source** → **Matrix**

Then decide **who owns each dimension**, and choose generators that reflect that ownership.

When ApplicationSets feel “complex”, it is almost always because **intent boundaries are unclear**, not because the generators are hard.

## Other ApplicationSet Generators (for completeness)

In addition to the generators discussed above, Argo CD provides **other specialized ApplicationSet generators** that exist for **advanced or niche use cases**.

These are **used far less frequently** than the generators covered in this chapter, but are mentioned here for **completeness and awareness**.

* **Merge generator**
  The Merge generator may be used to merge the generated parameters of two or more generators. Additional generators can override the values of the base generator.

* **SCM Provider generator**
  The SCM Provider generator uses the API of an SCM provider (for example, GitHub) to automatically discover repositories within an organization.

* **Pull Request generator**
  The Pull Request generator uses the API of an SCMaaS provider (for example, GitHub) to automatically discover open pull requests within a repository.

* **Cluster Decision Resource generator**
  The Cluster Decision Resource generator is used to interface with Kubernetes custom resources that apply custom logic to decide which set of Argo CD clusters to deploy to.

* **Plugin generator**
  The Plugin generator makes RPC or HTTP requests to external systems to obtain parameters dynamically.

---

> **Note:**
> Most real-world GitOps platforms rely primarily on **list, cluster, git, and matrix generators**.
> The generators listed above are typically introduced only in **highly automated or platform-heavy environments**.

---

# Conclusion

ApplicationSets shift GitOps from **managing individual deployments** to **managing deployment intent at scale**.

Rather than manually creating and maintaining dozens or hundreds of Argo CD Applications, ApplicationSets allow you to define **what should exist**, and let Argo CD continuously enforce that state as clusters, environments, and repositories evolve.

Across this walkthrough, we explored how ApplicationSets:

* eliminate YAML duplication
* reduce configuration drift
* react automatically to platform changes
* scale cleanly across clusters, regions, and environments

More importantly, we learned that **generators are not just syntax**.
They encode architectural decisions about **who owns deployment intent** and **where that intent lives**.

Whether intent is:

* explicitly defined in YAML
* inferred from cluster inventory
* derived from Git structure
* declared as configuration data
* or composed across multiple dimensions

ApplicationSets provide a first-class, declarative way to express it.

There is no universal “best” generator.
Strong GitOps platforms succeed not by memorizing generators, but by **choosing the one that matches their operational reality**.

Once that alignment is correct, ApplicationSets become not just a convenience, but a foundational building block for scalable, production-grade GitOps.

---

# References

Use these links to go deeper, validate concepts, and explore official behavior and edge cases.

* Argo CD ApplicationSet documentation
  [https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/)

* ApplicationSet generator reference
  [https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/)

* Argo CD architecture and concepts
  [https://argo-cd.readthedocs.io/en/stable/architecture/](https://argo-cd.readthedocs.io/en/stable/architecture/)

* GitOps principles (Weaveworks)
  [https://www.weave.works/technologies/gitops/](https://www.weave.works/technologies/gitops/)

* Kubernetes multi-cluster patterns
  [https://kubernetes.io/docs/concepts/cluster-administration/](https://kubernetes.io/docs/concepts/cluster-administration/)

---