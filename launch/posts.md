# Copy-ready launch drafts

## GitHub / short English

SchemaSnap is “Git diff for data”: a local Python CLI that snapshots CSV, Parquet, Arrow, or DuckDB
SQL and reports deterministic INFO/WARNING/BREAKING contract drift. Snapshots contain no raw rows,
string samples, category labels, SQL, or absolute paths. v0.1.0 ships with 69+ tests, a Broken Data
Gallery, Markdown CI reports, and an Apache-2.0 license.

## HelloGitHub / Chinese

SchemaSnap 是一个“给数据做 Git diff”的本地 CLI。它支持 CSV、Parquet、Arrow 和受限的
DuckDB SQL，把列类型、空值率、唯一率、分位数、时区和无标签类别分布保存成可进 Git 的稳定快照，
再用固定规则输出 INFO / WARNING / BREAKING。项目不上传数据、不调用大模型，也不把原始行、字符串、
类别标签或 SQL 写进快照。仓库提供中英文 README、破损数据样例库、GitHub Actions 模板和完整测试。

## LINUX DO / technical build log

标题：我做了一个隐私优先的数据契约 CLI：SchemaSnap（Git diff for data）

我想解决的是一个很小但常见的问题：Parquet/CSV 在 PR 里变了，代码 diff 看不见数据契约。SchemaSnap
会生成稳定 JSON，再对删除列、类型、新空值、时区、范围、类别形状和明显分布漂移做确定性判断。

最难的取舍是隐私：类别标签和字符串样本一律不落盘，只保存排序频率、基数和熵。这意味着“等频标签替换”
会故意漏报，但 Git 历史不会变成字符串字典。DuckDB 也只允许单条 SELECT/WITH，数据库只读且关闭外部访问。

欢迎用仓库里的 Broken Data Gallery 复现并挑错，尤其希望收到规则阈值、Arrow 兼容和隐私边界方面的反馈。

## Hacker News / Show HN

Title: Show HN: SchemaSnap – privacy-first, Git-native data contract diffs

SchemaSnap is a small local CLI for reviewing schema and aggregate distribution drift in pull requests.
It supports CSV, Parquet, Arrow IPC, and restricted read-only DuckDB SQL. The artifact is deterministic
JSON and intentionally excludes raw strings, category labels, SQL, absolute paths, and row samples.
The tradeoff is explicit: equal-frequency category-label replacement cannot be detected. Feedback on
the format and thresholds is welcome.
