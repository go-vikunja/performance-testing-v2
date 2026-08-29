# Findings: seeding 100 users / 48k tasks (2026-08-29, before the baseline run)

## 1. Task writes cost O(saved-filter kanban views on the instance)

`updateTasksInSavedFilterViews` (`pkg/models/listeners.go`) runs on every task create/update event. It
loads every saved-filter kanban view on the instance and, per task, runs one `Exist` query per view
(`addTaskToFilter`, `pkg/models/saved_filters.go`). Every user gets a default "My Open Tasks" filter
(`done = false && assignees = <username>`) with such a view, so cost per task write grows with the user count.

Observed while seeding 100 users / 48k tasks: Postgres pinned at 4 cores; in 40 s `pg_stat_statements`
counted 1,021,631 calls of

```
SELECT ... FROM tasks WHERE tasks.done=$1 AND EXISTS (SELECT 1 FROM task_assignees INNER JOIN users
  ON users.id = user_id WHERE tasks.id = task_id AND username IN ($2)) AND id=$3 ... LIMIT $6
```

each returning 0 rows (0.04 ms each; the count is the problem).

Fix direction: evaluate each filter once for the whole task batch (`id IN (...)`), and skip views whose
filter cannot match / whose owner cannot access the task's project.

## 2. Label permission check is expensive

`POST /tasks/{id}/labels` → `SELECT * FROM labels LEFT JOIN label_tasks ... WHERE labels.id=$1 AND
task_id IN (SELECT id FROM tasks WHERE project_id IN (<recursive accessible-projects CTE>))`: 17.7 ms mean,
top statement by total time during seeding. Expands the caller's whole project tree per call.

## 3. v2 token refresh cannot work with the cookie v2 login sets

`POST /api/v2/login` sets `vikunja_refresh_token` with `Path=/api/v1/user/token/refresh`
(`getRefreshTokenCookiePath`, `pkg/modules/auth/auth.go`). Browsers and cookie jars therefore never send it to
`POST /api/v2/user/token/refresh`, which answers 401 every time. Seen as 270 refresh failures in the baseline run.
Fixed in https://github.com/go-vikunja/vikunja/pull/3651 (merged 2026-08-29): one cookie per API version path.
