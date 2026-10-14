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
