### 1. GitHub

1. Create an empty repo (yours is `CI-CD_Databricks`).
2. **Token for Databricks → GitHub:** Profile → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**. Tick **`repo`** and **`workflow`**, then copy the token.
3. **Secrets for GitHub → Databricks:** Repo → **Settings → Secrets and variables → Actions → New repository secret**:

   * `DATABRICKS_HOST` = your workspace URL (`https://dbc-xxxx.cloud.databricks.com`)
   * `DATABRICKS_TOKEN` = a Databricks token (Databricks → **Settings → Developer → Access tokens → Generate**)

### 2. Databricks: Connect to GitHub

1. Profile icon → **Settings → Linked accounts → Add Git credential**: GitHub, **Personal access token**, username `Faiz-Kounain`, paste the GitHub token.
2. SQL editor, create the dev and prod “environments”:

```sql
CREATE SCHEMA IF NOT EXISTS workspace.dev_sales;
CREATE SCHEMA IF NOT EXISTS workspace.prod_sales;
```

### 3. Databricks: Git Folder

**Workspace → Your user folder → Create → Git folder** → Paste the repo URL. The **main** label appears next to it. Never touch the `.git` folder inside it.

### 4. Project Structure (Create → Folder / Create → File)

```text
CI-CD-v2/
├── databricks.yml               job + dev/prod settings
├── src/transforms.py            the logic (testable)
├── src/build_daily_sales.py     what the job runs
├── tests/test_transforms.py     unit test
└── .github/workflows/
    ├── ci.yml                   runs on Pull Request: pytest + bundle validate
    └── cd.yml                   runs on push to main: bundle deploy + run
```

The final `prod` target in `databricks.yml`:

```yaml
prod:
  mode: production
  workspace:
    root_path: /Workspace/Users/fk81307@gmail.com/.bundle/${bundle.name}/${bundle.target}
  variables:
    schema: prod_sales
```

And the environment `client: "2"`.

### 5. Push (Web Terminal)

```bash
cd CI-CD-v2
git add -A
git commit -m "message"
git push
```

### 6. What Happens Automatically

* **Push to main → CD:** `bundle deploy -t prod` creates or updates `daily_sales_job_prod`, then `bundle run` runs it and writes `workspace.prod_sales.daily_sales`.
* **Pull Request → CI:** Runs the tests and validates the bundle before anything reaches prod.

### 7. Check

* GitHub **Actions** tab: CD is green.
* Databricks **Jobs & Pipelines**: `daily_sales_job_prod` succeeded.
* `SELECT * FROM workspace.prod_sales.daily_sales;` returns 2 rows.


**CI (Continuous Integration): every time you push code, a robot checks it automatically by running tests and validating config. Bad code is caught before it ships.
CD (Continuous Deployment): when the code is approved (merged), the robot deploys it automatically to Databricks. No manual copy-paste.**

# Databricks CI/CD – My Notes

## 1. Architecture (big picture)

```text
┌──────────────────────────── DEVELOPER ────────────────────────────┐
│  Databricks Git folder / VS Code                                   │
│  feature branch: feature/JIRA-123                                  │
│  edit notebooks / .py / databricks.yml                             │
│  test in DEV:  databricks bundle deploy -t dev / bundle run -t dev │
└───────────────┬───────────────────────────────────────────────────┘
                │ git push
                ▼
┌──────────────────────── GIT (GitHub / Azure Repos) ───────────────┐
│  main (protected: no direct push)                                  │
│  Pull Request  ──► reviewers approve                               │
└───────────────┬───────────────────────────────────────────────────┘
                │ PR opened / updated                │ merged to main
                ▼                                    ▼
┌──────── CI (GitHub Actions / Azure Pipelines) ┐  ┌──────── CD ─────────────────────────────┐
│ runner (temporary Linux VM)                   │  │ runner (temporary Linux VM)             │
│ 1. checkout code                              │  │ 1. checkout code                        │
│ 2. pytest (local PySpark, no Databricks)      │  │ 2. install Databricks CLI               │
│ 3. lint / format                              │  │ 3. login as SERVICE PRINCIPAL (secrets) │
│ 4. databricks bundle validate                 │  │ 4. bundle deploy -t qa  (auto)          │
│ red ❌ → merge blocked                         │  │ 5. ⏸ manual APPROVAL (prod environment) │
│ green ✅ → merge allowed                       │  │ 6. bundle deploy -t prod                │
└───────────────────────────────────────────────┘  │ 7. bundle run (smoke test, optional)    │
                                                   └───────────┬─────────────────────────────┘
                                                               │ Databricks REST API
                     ┌─────────────────────────────────────────┼───────────────────────┐
                     ▼                                         ▼                       ▼
            ┌──── DEV workspace ────┐        ┌──── QA workspace ────┐     ┌──── PROD workspace ────┐
            │ [dev name] jobs       │        │ jobs_qa              │     │ jobs_prod              │
            │ dev_catalog / schema  │        │ qa_catalog           │     │ prod_catalog           │
            │ per-developer copies  │        │ test data, QA checks │     │ scheduled, monitored   │
            └───────────────────────┘        └──────────────────────┘     └────────────────────────┘

Secrets: GitHub Secrets / ADO Variable groups ← Azure Key Vault
Identity: humans → dev only; service principal → QA + prod
```

### What the bundle deploy actually does
```text
databricks.yml + resources/*.yml
        │  bundle deploy -t prod
        ▼
1. Upload files (notebooks, .py) → /Workspace/.../.bundle/<name>/prod/files
2. Create or update jobs/pipelines exactly as written in YAML
3. Save deployment state (so the next deploy updates instead of duplicating)
```

### In Free Edition (my practice)
- One workspace only → dev and prod faked as schemas: `dev_sales`, `prod_sales`.
- Auth = personal access token (company = service principal).

## 2. The 3 tools
| Tool | What it does |
|---|---|
| **Git folder** (Workspace → Create → Git folder) | Links workspace to a GitHub repo: pull, commit, push, branch from Databricks |
| **Asset Bundles** (`databricks.yml`) | Jobs, pipelines, settings written as code; deployed with one command; targets like dev/prod |
| **GitHub Actions / Azure Pipelines** | The robot that runs tests (CI) and deploys (CD) |

## 3. One-time setup
1. Create empty GitHub repo.
2. **GitHub token (for Databricks → GitHub):** GitHub → Settings → Developer settings → Tokens (classic) → tick **repo** + **workflow**.
3. Databricks → Settings → **Linked accounts** → Add Git credential → GitHub → Personal access token → username + token.
4. **Databricks token (for GitHub → Databricks):** Databricks → Settings → Developer → Access tokens → Generate.
5. GitHub repo → Settings → Secrets and variables → Actions:
   - `DATABRICKS_HOST` = workspace URL
   - `DATABRICKS_TOKEN` = Databricks token
6. Create environments:
```sql
CREATE SCHEMA IF NOT EXISTS workspace.dev_sales;
CREATE SCHEMA IF NOT EXISTS workspace.prod_sales;
```
7. Workspace → Create → **Git folder** → repo URL. Never touch the `.git` folder.

## 4. Repo structure
```text
CI-CD-v2/
├── databricks.yml              ← bundle: jobs + dev/prod targets
├── src/
│   ├── transforms.py           ← pure logic (testable)
│   └── build_daily_sales.py    ← job entry point
├── notebooks/
│   ├── 01_bronze.ipynb
│   ├── 02_silver.ipynb
│   └── 03_gold.ipynb
├── tests/
│   └── test_transforms.py      ← unit tests
└── .github/workflows/
    ├── ci.yml                  ← runs on Pull Request
    └── cd.yml                  ← runs on push/merge to main
```

## 5. Code

### src/transforms.py
```python
from pyspark.sql import DataFrame, functions as F

def daily_sales(orders: DataFrame) -> DataFrame:
    return (orders
            .filter(F.col("amount") > 0)              # drop bad rows
            .groupBy("order_date")
            .agg(F.sum("amount").alias("revenue"),
                 F.count("*").alias("orders")))
```

### src/build_daily_sales.py
```python
import sys
from pyspark.sql import SparkSession
from transforms import daily_sales

schema = sys.argv[1]          # dev_sales or prod_sales, passed by the bundle
spark = SparkSession.builder.getOrCreate()

orders = spark.createDataFrame(
    [("2026-10-13", 100.0), ("2026-10-13", 50.0), ("2026-10-14", 70.0), ("2026-10-14", -5.0)],
    "order_date STRING, amount DOUBLE")

daily_sales(orders).write.mode("overwrite").saveAsTable(f"workspace.{schema}.daily_sales")
print(f"Wrote workspace.{schema}.daily_sales")
```

### tests/test_transforms.py
```python
import sys; sys.path.append("src")
from pyspark.sql import SparkSession
from transforms import daily_sales

def test_daily_sales_drops_negative_and_sums():
    spark = SparkSession.builder.master("local[1]").getOrCreate()
    df = spark.createDataFrame(
        [("d1", 100.0), ("d1", 50.0), ("d1", -5.0)], "order_date STRING, amount DOUBLE")
    row = daily_sales(df).collect()[0]
    assert row.revenue == 150.0
    assert row.orders == 2
```

### Notebooks (parameters via widgets)
```python
dbutils.widgets.text("schema", "dev_sales")
schema = dbutils.widgets.get("schema")
```

## 6. databricks.yml (final working version)
```yaml
bundle:
  name: ci-cd-demo

variables:
  schema:
    default: dev_sales

resources:
  jobs:
    daily_sales_job:                       # .py job
      name: daily_sales_job_${bundle.target}
      tasks:
        - task_key: build
          spark_python_task:
            python_file: src/build_daily_sales.py
            parameters: ["${var.schema}"]
          environment_key: default
      environments:
        - environment_key: default
          spec:
            client: "2"                    # serverless environment version

    orders_pipeline:                       # notebook job with dependencies
      name: orders_pipeline_${bundle.target}
      tasks:
        - task_key: bronze
          notebook_task:
            notebook_path: notebooks/01_bronze.ipynb
            base_parameters: { schema: "${var.schema}" }
          environment_key: default
        - task_key: silver
          depends_on: [{ task_key: bronze }]
          notebook_task:
            notebook_path: notebooks/02_silver.ipynb
            base_parameters: { schema: "${var.schema}" }
          environment_key: default
        - task_key: gold
          depends_on: [{ task_key: silver }]
          notebook_task:
            notebook_path: notebooks/03_gold.ipynb
            base_parameters: { schema: "${var.schema}" }
          environment_key: default
      environments:
        - environment_key: default
          spec:
            client: "2"

targets:
  dev:
    mode: development          # [dev name] prefix, schedules paused, files in my user folder
    default: true
    variables:
      schema: dev_sales
  prod:
    mode: production
    workspace:
      root_path: /Workspace/Users/<my-email>/.bundle/${bundle.name}/${bundle.target}   # required in production mode
    variables:
      schema: prod_sales
    # company: run_as: { service_principal_name: "<sp-app-id>" }
```
- No cluster defined → runs on **serverless**.
- `.py` → `spark_python_task` + `sys.argv`. Notebook → `notebook_task` + `base_parameters` + widgets.
- Many jobs → `include: [resources/*.yml]`, one file per job.

## 7. ci.yml
```yaml
name: CI
on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
      DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: "17" }
      - run: pip install pyspark==3.5.1 pytest
      - run: pytest -q                              # 1. unit tests
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate -t prod     # 2. config is valid
```

## 8. cd.yml
```yaml
name: CD
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
      DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle deploy -t prod
      - run: databricks bundle run -t prod daily_sales_job
      - run: databricks bundle run -t prod orders_pipeline
```

## 9. Useful commands (Web Terminal)
```bash
cd CI-CD-v2                                   # always go into the repo first
git status / git log --oneline
git add -A && git commit -m "msg" && git push
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev daily_sales_job
databricks bundle generate job --existing-job-id <id>   # turn a UI job into YAML
```

## 10. Pull Request flow (practised)
1. `git checkout main && git pull && git checkout -b feature/min-amount`
2. Change `transforms.py` → `.filter(F.col("amount") > 60)`
3. `git add -A && git commit -m "only count orders above 60" && git push -u origin feature/min-amount`
4. GitHub → **Compare & pull request** → Create PR → CI runs.
5. **CI red ❌**: `assert 100.0 == 150.0`. The old test caught the behaviour change.
6. Intended change → update test: `revenue == 100.0`, `orders == 1` → push → CI green ✅.
7. Reviewer checks **Files changed** (code + test) → **Merge**.
8. Merge = push to main → **CD** deploys to prod.
9. Cleanup: `git checkout main && git pull && git branch -d feature/min-amount`

**Key idea:** developers write code **and** tests. CI only runs them. Intended change = update code + test together.

## 11. Day-to-day flow in a company
1. Jira ticket.
2. `git checkout -b feature/JIRA-123-...` from main.
3. Code in Git folder / VS Code.
4. Test in DEV: `bundle deploy -t dev` (own copy).
5. Push → Pull Request to main.
6. CI: pytest, lint, bundle validate (+ sometimes integration tests on sample data).
7. Code review + approval.
8. Merge to main.
9. CD → QA (automatic) → business/QA checks.
10. CD → PROD after **manual approval**, often in a release window.
11. Prod runs on schedule; monitoring + alerts.
12. Problem → rollback: `git revert` + CD redeploys the old version.

**Hotfix:** `hotfix/...` branch from main → fast PR → same pipeline, no shortcuts.

## 12. Scaling to 1000 pipelines
- **One YAML per job** in `resources/`, pulled in with `include`.
- **Bundles per domain/team** (sales/, finance/, …) + `shared/` library.
- **Path filters**: CI/CD runs only for the folder that changed (`paths: ["finance/**"]`).
- **Metadata-driven**: 1 generic notebook + config file of tables instead of 1000 notebooks.
- Generate YAML from existing UI jobs with `bundle generate job`.
- For SAS migration: add a **reconciliation task** (PySpark output = SAS output).

## 13. Service principals
- Robot account for automation: no person, no UI login.
- Why not a personal token: breaks when you leave, too much power, wrong audit trail.
- Gets least-privilege access (deploy + write prod only).
- Secrets: `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` (CLI picks them up automatically).
- Job runs as SP: `run_as: { service_principal_name: ... }`.
- Azure: SP lives in **Microsoft Entra ID**. Best: **OIDC / workload identity federation** (no stored secret).

| | Personal token | Service principal |
|---|---|---|
| Tied to a person | Yes | No |
| Permissions | Everything I have | Only what's needed |
| Audit | "Nani did it" | "cicd robot did it" |
| Use | Dev / learning | Prod deployments |

## 14. Azure DevOps (ADO)
| GitHub | Azure DevOps |
|---|---|
| Repository | Azure Repos |
| Pull Request | Pull Request |
| GitHub Actions `.github/workflows/*.yml` | Azure Pipelines `azure-pipelines.yml` |
| Secrets | Variable groups (+ Azure Key Vault) |
| Environments + required reviewers | Environments + Approvals and checks |
| Branch protection | Branch policies |

- Pipeline = **stages** (CI → Deploy_QA → Deploy_Prod) → **jobs** → **steps**.
- `deployment` job + `environment: prod` → approval pause.
- Approval setup: Pipelines → Environments → prod → Approvals and checks.
- GitHub equivalent: Settings → Environments → prod → Required reviewers.
- `databricks.yml` and notebooks don't change, only the pipeline file.

## 15. One line per part
- **Git folder:** where I write and branch code in Databricks.
- **Pull Request:** "can this go to prod?"
- **CI:** "is it safe?" (tests + validate)
- **Merge:** a human says yes.
- **CD:** a robot deploys the same way every time.
- **Targets:** same code to dev/prod, only settings change.
- **Service principal:** the robot's identity.
- **Approval:** final human gate before prod.

## 16. Interview answer
"We keep jobs as code with Databricks Asset Bundles and develop on feature branches in Git folders. A Pull Request triggers CI: pytest on pure PySpark functions, linting, and `bundle validate`. After review and merge, CD deploys to QA automatically and to prod after a manual approval, using a service principal with least privilege, with secrets from Key Vault or OIDC. Environments are separate workspaces or catalogs, large projects split jobs into one YAML per job and bundles per domain, and nobody changes prod by hand."


Part 1: What is CI/CD
🗣️ “CI/CD automates how code goes from a developer’s laptop to production.
• CI (Continuous Integration): every time someone pushes code or opens a PR, it’s automatically checked (validated, tested, reviewed) before it’s merged. That catches problems early.
• CD (Continuous Delivery/Deployment): once code is merged, it’s deployed automatically and the same way every time, first to dev and then, after approval, to prod.
For data engineering, the main value is that pipelines are versioned, reviewed and repeatable. Nobody edits jobs by hand in the UI, so dev and prod stay the same, and you can always trace or roll back a change.”

Part 2: How I did it in my project
CI/CD is how code goes from a developer’s laptop to production automatically and safely. I make changes on a feature branch, push to GitHub and open a pull request. That triggers CI: a GitHub Actions workflow installs the dependencies, runs linting and the pytest unit tests, and validates the bundle. If everything passes, another developer reviews and approves the PR, and it’s merged to main.

The merge triggers CD: a second workflow runs databricks bundle deploy. The job’s notebooks, task order and cluster settings are all defined in databricks.yml, so the job is created or updated automatically, first in dev and then in prod. Nobody changes jobs by hand in the UI, so every change is reviewed, tested and traceable.”
| File                      | Is it DAB?                               | What it does                                                                                | Who reads it                                |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `databricks.yml`          | ✅ **Yes, this is the DAB (bundle) file** | **WHAT** to deploy: the job, its notebooks/tasks, task order, cluster, and dev/prod targets | Databricks CLI (`databricks bundle deploy`) |
| `.github/workflows/*.yml` | ❌ No, this is **GitHub Actions**         | **WHEN and HOW** to run: on a PR, run pytest. On merge to main, run `bundle deploy`         | GitHub                                      |





just give plain md text text

```
Here are the CI/CD questions interviewers usually ask, with short answers 👇

**Basics**
1. **CI vs Continuous Delivery vs Continuous Deployment?** CI = auto-check every change. Delivery = always ready to deploy, but prod needs a manual approval. Deployment = goes to prod automatically.
2. **Why CI/CD for data pipelines?** No manual UI edits, the same code in dev and prod, every change is reviewed and traceable, and rollback is easy.
3. **What are Databricks Asset Bundles?** A way to define jobs, clusters and notebooks as code in `databricks.yml`, then `validate` and `deploy` them with the CLI.

**Your project**
4. **What happens when you open a PR?** GitHub Actions runs `bundle validate` (plus tests if you add them). The merge happens only if the checks pass.
5. **What happens on merge to main?** A workflow runs `databricks bundle deploy`, which creates or updates the job.
6. **How did GitHub Actions log in to Databricks?** With the host and token stored as encrypted GitHub secrets, which are read as environment variables.
7. **How do you deploy to different environments?** With bundle **targets** (dev and prod), each with its own workspace, settings and parameters.

**Senior level ⭐**
8. **Why not use a personal token in prod?** It's tied to one person, it expires, and it has too much access. Use a service principal with OIDC instead.
9. **How do you test PySpark code?** Use pytest with a small SparkSession, build input DataFrames, and compare the expected and actual output. Add data quality checks too.
10. **A deployment broke prod. What do you do?** Roll back by redeploying the last good commit, find the root cause, and add a test or check that would have caught it.
11. **How do you stop someone deploying untested code?** Use branch protection, required reviewers, required status checks and a manual approval for prod.
12. **How do you manage secrets in notebooks?** Use Databricks secret scopes with `dbutils.secrets.get()`, never hardcoded values.
13. **What's your branching strategy?** Feature branches, PRs to main, and main is always deployable (trunk-based). Use release tags if needed.
14. **Bundles vs Terraform?** Bundles handle the jobs and code. Terraform handles the workspace infrastructure (workspaces, catalogs, permissions).


```
