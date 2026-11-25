# Automated Deployment with Databricks Asset Bundles

Deploying Databricks jobs, pipelines, and notebooks the same way as application code: packaged as **Databricks Asset Bundles (DABs)**, version-controlled, promoted between environments, and released through CI/CD.

---

## What is covered

* Creating a bundle from a template and deploying a simple job to a workspace
* Targeting **multiple environments** (development / staging / production) from one bundle definition
* Using the **default Databricks bundle template** as a starting point
* **CI/CD with DABs** — validating and deploying bundles from a pipeline
* Adding **machine learning** workloads to engineering workflows
* Developing against a workspace from **VS Code** with Databricks

---

## Notebooks

| Notebook | Type | Description |
|----------|------|-------------|
| `Lab - Deploy a Simple DAB.ipynb` | Lab | Build and deploy a minimal bundle |
| `Lab - Deploy a DAB to Multiple Environments.ipynb` | Lab | Promote the same bundle across environments |
| `Lab - Use a Databricks Default DAB Template.ipynb` | Lab | Scaffold a project with the default template |
| `Lab - Adding ML to Engineering Workflows with DABs.ipynb` | Lab | Include an ML workload in the bundle |
| `Demo - Deploying a DAB to Multiple Environments.ipynb` | Demo | Instructor walkthrough of multi-environment deploys |
| `Demo - CICD with DABs.ipynb` | Demo | Wiring bundle validation and deployment into CI/CD |
| `08 - Using VSCode with Databricks.ipynb` | Reference | Local development workflow |

---

## Bundle sources

The `.zip` files are the bundle projects referenced by the labs, numbered to match the notebook order:

| Archive | Purpose |
|---------|---------|
| `01 - Deploying a Simple DAB.zip` | Starting point for the simple deployment |
| `02L - Deploy a Simple DAB.zip` | Solution for the simple deployment lab |
| `03 - Deploying a DAB to Multiple Environments.zip` | Multi-environment starting point |
| `04L - Deploy a DAB to Multiple Environments.zip` | Multi-environment lab solution |
| `05L - Use a Databricks Default DAB Template.zip` | Solution using the default template |
| `07L Bonus - Adding ML to Engineering Workflows with DABs.zip` | Bonus ML-in-bundle solution |

---

## Prerequisites

* Databricks CLI authenticated against your workspace (`databricks auth login`)
* A Databricks personal access token stored in a profile
* A Git repository if you follow the CI/CD demo
* Unity Catalog enabled, so bundle-defined catalogs/schemas can be created

---

## Running the labs

```bash
# Unzip the bundle for the lab you are working on
unzip "04L - Deploy a DAB to Multiple Environments.zip"

# Validate, then deploy to a target defined in databricks.yml
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev <resource_name>
```

---

## Tools & Technologies

* Databricks Asset Bundles, Databricks CLI
* GitHub Actions (CI/CD demo)
* VS Code with the Databricks extension
* Unity Catalog, Delta Live Tables
