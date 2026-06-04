# Git 学习笔记

这个文档用来记录本项目中实际执行过的 Git 操作。它不是单纯的命令清单，而是为了帮助你理解：

- 我用了什么 Git 命令
- 每个命令的作用是什么
- 为什么要这样做
- 遇到了什么问题
- 问题是怎么解决的
- 之后你自己做项目时可以怎么复用

之后每次我完成 `git add`、`git commit`、`git push` 或处理 Git 异常后，都会自动更新这个文档。

## 2026-06-04：Day 1 初始化仓库、首次提交并推送到 GitHub

### 本次 Git 目标

Day 1 代码已经完成并通过 review，所以这次 Git 操作的目标是：

1. 把当前项目目录变成 Git 仓库
2. 排除不应该提交的本地文件
3. 提交 Day 1 的 FastAPI 工程骨架
4. 连接到 GitHub 远程仓库
5. 推送到 GitHub 的 `main` 分支

远程仓库地址：

```text
git@github.com:Thelcn/enterprise-rag-copilot.git
```

### 1. 查看当前目录是否已经是 Git 仓库

执行命令：

```powershell
git status --short
```

结果：

```text
fatal: not a git repository (or any of the parent directories): .git
```

这说明当前目录还不是 Git 仓库。

通俗理解：Git 还没有开始“管理”这个文件夹，所以它不知道哪些文件新增了、哪些文件修改了、哪些文件要提交。

### 2. 新增 `.gitignore`

在初始化和提交前，我先创建了 `.gitignore`。

`.gitignore` 的作用是告诉 Git：哪些文件或目录不要追踪、不要提交。

本项目主要忽略了：

```text
__pycache__/
*.py[cod]
.pytest_cache/
pytest-cache-files-*/
.venv/
.env
```

这些内容为什么不能提交？

- `.venv/` 是本机 Python 虚拟环境，体积大，而且和别人的电脑不一定兼容
- `__pycache__/` 是 Python 运行后生成的缓存文件，不是源码
- `.pytest_cache/` 和 `pytest-cache-files-*/` 是 pytest 运行后的缓存
- `.env` 可能包含本地配置或密钥，不应该上传

但是 `.env.example` 可以提交，因为它只是模板，不包含秘密信息。

### 3. 初始化 Git 仓库

执行命令：

```powershell
git init
```

作用：在当前目录下创建 `.git/`，让 Git 开始管理这个项目。

第一次执行时遇到了问题：

```text
warning: unable to unlink 'G:/港城莞/Agent_study/enterprise-rag-copilot/.git/config.lock': Invalid argument
error: could not write config file G:/港城莞/Agent_study/enterprise-rag-copilot/.git/config: Permission denied
fatal: could not set 'core.repositoryformatversion' to '0'
```

问题原因：

Git 初始化过程中需要写 `.git/config`，但当时出现了 `.git/config.lock` 锁文件和权限问题，导致初始化没有完成。

解决方式：

```powershell
if (Test-Path -LiteralPath '.git\config.lock') {
    Remove-Item -LiteralPath '.git\config.lock' -Force -ErrorAction Stop
}
git init
```

这段命令做了两件事：

1. 如果 `.git/config.lock` 存在，就删除它
2. 重新执行 `git init`

第二次执行成功：

```text
Initialized empty Git repository in G:/港城莞/Agent_study/enterprise-rag-copilot/.git/
```

学习点：

Git 的 `.lock` 文件通常表示“某个 Git 操作正在进行”。如果 Git 操作异常中断，锁文件可能残留，后续 Git 操作就会失败。确认没有其他 Git 操作正在运行后，可以删除残留 lock 文件。

### 4. 检查 Git 用户信息

执行命令：

```powershell
git config user.name
git config user.email
```

结果：

```text
TimeLapse
80013972+Thelcn@users.noreply.github.com
```

作用：确认 Git commit 会使用哪个用户名和邮箱。

学习点：

每个 commit 都会记录作者信息。如果这里没有配置，`git commit` 可能会失败，或者使用你不想要的身份信息。

### 5. 查看将要提交的文件

执行命令：

```powershell
git status --short
```

当时看到的文件包括：

```text
?? .env.example
?? .gitignore
?? .learnings/
?? Dockerfile
?? README.md
?? app/
?? rag_copilot_week1_execution_plan.pdf
?? requirements.txt
?? tests/
```

`??` 的意思是：这些文件是 untracked，也就是 Git 还没有追踪过的新文件。

这一步很重要，因为提交前要确认没有把 `.venv/`、`__pycache__/`、pytest 缓存等不该提交的内容放进去。

### 6. 暂存文件

执行命令：

```powershell
git add .
```

作用：把当前目录下应该被 Git 追踪的变更加入 staging area。

通俗理解：

- 工作区：你正在编辑的文件
- 暂存区：准备进入下一次 commit 的文件
- commit：真正保存成一个 Git 历史版本

`git add .` 的意思是：把当前目录下所有没有被 `.gitignore` 排除的新增/修改文件放入暂存区。

第一次执行时遇到问题：

```text
fatal: Unable to create 'G:/港城莞/Agent_study/enterprise-rag-copilot/.git/index.lock': Permission denied
```

问题原因：

Git 需要写 `.git/index` 来记录暂存区状态，但 `.git/index.lock` 创建失败，仍然是 Windows 文件权限或锁文件相关问题。

解决方式：

使用提升权限重新执行：

```powershell
git add .
```

之后暂存成功。

同时 Git 提示了一批换行符 warning：

```text
LF will be replaced by CRLF the next time Git touches it
```

这不是错误。

它的意思是：当前文件使用 Unix 风格换行 `LF`，但 Windows 上 Git 可能会在工作区转换成 `CRLF`。这不会影响代码功能。

### 7. 确认暂存区内容

执行命令：

```powershell
git diff --cached --name-only
```

作用：只看已经进入暂存区、准备被 commit 的文件名。

当时确认进入暂存区的文件有：

```text
.env.example
.gitignore
.learnings/ERRORS.md
.learnings/day1_fastapi_skeleton_learning_notes.md
Dockerfile
README.md
app/api/routes.py
app/core/config.py
app/main.py
rag_copilot_week1_execution_plan.pdf
requirements.txt
tests/test_health.py
```

这一步的意义：

提交前最后确认“我要提交什么”。尤其是新项目第一次提交，很容易误把虚拟环境、缓存、临时文件提交进去。

### 8. 创建第一次 commit

执行命令：

```powershell
git commit -m "chore: initialize rag copilot fastapi skeleton"
```

作用：把暂存区里的内容保存成一个 Git 历史版本。

提交成功：

```text
[master (root-commit) 147e1cf] chore: initialize rag copilot fastapi skeleton
 12 files changed, 732 insertions(+)
```

这里有几个关键词：

- `master`：当时本地默认分支名
- `root-commit`：这个仓库的第一个 commit
- `147e1cf`：commit 的短 hash，可以理解为这次提交的 ID
- `12 files changed`：本次提交涉及 12 个文件

commit message 为什么这样写？

```text
chore: initialize rag copilot fastapi skeleton
```

- `chore` 表示工程初始化、配置、杂项建设
- `initialize rag copilot fastapi skeleton` 表示这次做的是 RAG Copilot 的 FastAPI 骨架初始化

好的 commit message 应该说明“做了什么”，最好还能暗示“为什么”。

### 9. 把本地分支改名为 `main`

执行命令：

```powershell
git branch -M main
```

作用：把当前分支强制重命名为 `main`。

为什么要这样做？

很多 GitHub 新仓库默认主分支叫 `main`。而本地 `git init` 后有时默认分支是 `master`。为了和 GitHub 保持一致，所以改成 `main`。

### 10. 添加 GitHub 远程仓库

执行命令：

```powershell
git remote add origin git@github.com:Thelcn/enterprise-rag-copilot.git
```

作用：给当前本地仓库添加一个名为 `origin` 的远程仓库。

通俗理解：

- 本地仓库：你电脑上的 Git 仓库
- 远程仓库：GitHub 上的仓库
- `origin`：远程仓库的常用默认名字

之后执行 `git push origin main` 时，Git 就知道要把 `main` 分支推到哪个 GitHub 仓库。

### 11. 推送到 GitHub

执行命令：

```powershell
git push -u origin main
```

作用：把本地 `main` 分支推送到 GitHub 的 `origin/main`。

成功结果：

```text
branch 'main' set up to track 'origin/main'.
To github.com:Thelcn/enterprise-rag-copilot.git
 * [new branch]      main -> main
```

这里的 `-u` 是 `--set-upstream` 的简写。

它的作用是建立本地 `main` 和远程 `origin/main` 的追踪关系。

之后你在这个分支上可以更简单地使用：

```powershell
git push
git pull
```

而不一定每次都写完整的 `git push origin main`。

### 12. 最后检查状态

执行命令：

```powershell
git status --short
git log --oneline --decorate -n 3
git remote -v
```

作用：

- `git status --short`：确认工作区是否干净
- `git log --oneline --decorate -n 3`：查看最近 3 个 commit
- `git remote -v`：确认远程仓库地址

最终状态：

```text
147e1cf (HEAD -> main, origin/main) chore: initialize rag copilot fastapi skeleton
```

说明：

- `HEAD -> main`：当前本地分支是 `main`
- `origin/main`：远程 GitHub 上的 `main` 分支也在这个 commit
- 本地和远程已经同步

## 本次 Git 操作的关键学习点

### `git status` 是最常用的安全检查

在执行 `add`、`commit`、`push` 前后都应该经常看：

```powershell
git status --short
```

它能帮你确认：

- 哪些文件未追踪
- 哪些文件已修改
- 哪些文件已暂存
- 当前是否还有未提交内容

### `.gitignore` 应该尽早创建

如果先 `git add .`，再发现 `.venv/` 或缓存被加进去了，就需要额外清理。

新项目中最好先写 `.gitignore`，再 `git add .`。

### `git add` 不是提交

`git add` 只是把文件放进暂存区。

真正生成历史版本的是：

```powershell
git commit -m "message"
```

### `git push` 是把本地 commit 上传到 GitHub

本地 commit 只存在你的电脑上。

只有 push 后，GitHub 仓库才会看到这些提交。

### 处理 `.lock` 文件要谨慎

这次遇到了：

- `.git/config.lock`
- `.git/index.lock`

它们一般表示 Git 正在执行某个操作。

只有在确认没有其他 Git 命令正在运行时，才可以删除残留 lock 文件。不要随便删除 `.git/` 里的其他文件。

## 之后我会怎么维护这个文档

之后每次完成 Git 操作后，我会在这里追加一节，至少记录：

- 日期和任务名
- 执行的 Git 命令
- 每条命令的作用
- commit message
- 是否 push
- 遇到的问题和解决方式
- 你需要理解的 Git 学习点

这样这个文件会逐渐变成你自己的项目 Git 实战笔记。

## 2026-06-04：Day 2 提交 `/chat` API 契约

### 本次 Git 目标

Day 2 已经完成并通过测试，本次 Git 操作的目标是：

1. 查看当前工作区有哪些改动
2. 把 Day 2 的 schema、mock `/chat`、API 契约文档、测试和学习笔记放入暂存区
3. 创建一个 Day 2 commit
4. 推送到 GitHub 的 `main` 分支
5. 确认本地和远程同步

这次会把之前新增但尚未提交的 `git_learning_notes.md` 一起纳入提交。这样 Git 学习记录本身也会被保存在仓库历史里。

### 1. 查看当前工作区状态

执行命令：

```powershell
git status --short
```

作用：快速查看当前有哪些文件被修改、新增、删除。

本次看到的状态包括：

```text
 M .learnings/ERRORS.md
 M app/api/routes.py
?? .learnings/day2_chat_contract_learning_notes.md
?? .learnings/git_learning_notes.md
?? app/schemas/
?? docs/
?? tests/test_chat_contract.py
```

这里的含义：

- `M` 表示 modified，也就是已经被 Git 追踪过，现在发生了修改
- `??` 表示 untracked，也就是新文件或新目录，Git 还没有追踪

学习点：

提交前一定要先看 `git status --short`。这一步可以避免把不该提交的文件误加进去。

### 2. 查看最近提交历史

执行命令：

```powershell
git log --oneline --decorate -n 5
```

作用：查看最近 5 条 commit，并显示分支和远程指针位置。

本次看到：

```text
147e1cf (HEAD -> main, origin/main, origin/HEAD) chore: initialize rag copilot fastapi skeleton
```

说明当前本地 `main` 和远程 `origin/main` 都停在 Day 1 commit 上。Day 2 还没有提交。

### 3. 暂存 Day 2 文件

执行命令：

```powershell
git add .
```

作用：把当前目录下所有未被 `.gitignore` 排除的改动加入暂存区。

通俗理解：

`git add .` 不是提交，它只是告诉 Git：“这些改动我准备放进下一次 commit。”

本次应进入暂存区的主要内容：

- `app/schemas/evidence.py`
- `app/schemas/trace.py`
- `app/schemas/chat.py`
- `app/api/routes.py`
- `docs/contracts/query_api.md`
- `tests/test_chat_contract.py`
- `.learnings/day2_chat_contract_learning_notes.md`
- `.learnings/git_learning_notes.md`
- `.learnings/ERRORS.md`

注意：`.venv/`、`__pycache__/`、pytest cache 不会被提交，因为 `.gitignore` 已经排除了它们。

### 4. 确认暂存区内容

执行命令：

```powershell
git diff --cached --name-only
```

作用：只列出已经进入暂存区、即将被 commit 的文件。

学习点：

这个命令适合在 `git add .` 之后、`git commit` 之前使用。它相当于提交前的“最后点名”。

### 5. 创建 Day 2 commit

执行命令：

```powershell
git commit -m "feat: define chat api contract"
```

作用：把暂存区的改动保存成一个新的 Git 历史版本。

这次 commit message 的含义：

- `feat` 表示新增功能
- `define chat api contract` 表示这次新增的是 `/chat` API 契约

为什么这里用 `feat`？

因为 Day 2 不只是文档或配置调整，而是新增了用户可访问的 `POST /chat` API 结构。

### 6. 推送到 GitHub

执行命令：

```powershell
git push
```

作用：把本地 Day 2 commit 上传到 GitHub。

因为 Day 1 已经执行过：

```powershell
git push -u origin main
```

本地 `main` 已经和远程 `origin/main` 建立了 tracking 关系，所以这次可以直接使用更短的：

```powershell
git push
```

学习点：

第一次推送某个分支时常用：

```powershell
git push -u origin main
```

之后在同一个分支上继续推送，通常可以直接：

```powershell
git push
```

### 7. 推送后检查状态

执行命令：

```powershell
git status --short
git log --oneline --decorate -n 5
```

作用：

- 确认工作区是否干净
- 确认 `HEAD -> main` 和 `origin/main` 是否指向最新 commit

如果 `git status --short` 没有输出，说明当前没有未提交内容。

如果 `git log` 里最新一行同时显示：

```text
HEAD -> main, origin/main
```

说明本地和 GitHub 已经同步到同一个 commit。

### 本次 Git 学习点

### 为什么要先更新 Git 学习文档再 commit

你希望每次 Git 提交后都维护这个学习文档。为了避免出现“提交完再改文档，然后文档又变成未提交”的循环，本项目采用这个做法：

1. 提交前先把本次 Git 操作会使用的命令和学习点写进文档
2. 把代码、测试、项目学习笔记、Git 学习笔记一起提交
3. 提交和推送后的最终 commit hash 与结果在对话中向你汇报

这样既能让 Git 学习文档进入仓库历史，又不会制造一个永远多出来的未提交文档修改。

### `git add .` 前一定先看 `.gitignore`

如果 `.gitignore` 没有配置好，`git add .` 可能会把 `.venv/`、缓存文件、临时文件一起加入暂存区。

本项目 Day 1 已经补了 `.gitignore`，所以 Day 2 可以安全使用 `git add .`。

### commit message 要能说明这次变化的主题

这次使用：

```text
feat: define chat api contract
```

它比 “update files” 更好，因为它告诉 reviewer：

- 这次是一个 feature
- feature 的主题是 chat API contract

好的 commit message 会让后续查历史、写简历、做项目复盘都更轻松。

## 2026-06-04：Day 3 提交电商 demo 数据和通用 document loader

### 本次 Git 目标

Day 3 已完成并通过测试，本次 Git 操作的目标是：

1. 查看 Day 3 新增了哪些文件
2. 把电商 mock 数据、policy 文档、Document schema、document loader、ecommerce adapter、测试和 Day 3 学习笔记加入暂存区
3. 创建 Day 3 commit
4. 推送到 GitHub
5. 确认本地 `main` 和远程 `origin/main` 同步

### 1. 查看当前工作区状态

执行命令：

```powershell
git status --short
```

本次看到：

```text
?? .learnings/day3_document_loader_learning_notes.md
?? app/domains/
?? app/pipeline/
?? app/schemas/document.py
?? data/
?? tests/test_document_loader.py
```

这里全部都是 `??`，表示这些都是 Git 还没有追踪的新文件或新目录。

学习点：

`??` 不是错误，它只是提醒你：这些文件还没有进入 Git 历史。如果要提交它们，需要先执行 `git add`。

### 2. 查看最近提交历史

执行命令：

```powershell
git log --oneline --decorate -n 5
```

本次看到：

```text
b2d1762 (HEAD -> main, origin/main, origin/HEAD) feat: define chat api contract
147e1cf chore: initialize rag copilot fastapi skeleton
```

这说明：

- 当前本地分支是 `main`
- 远程 `origin/main` 和本地 `main` 都在 Day 2 commit 上
- Day 3 还没有提交

### 3. 为什么 `git diff --stat` 没有输出

执行命令：

```powershell
git diff --stat
```

本次没有输出。

这容易让初学者误以为“没有改动”，但其实不是。

原因是：`git diff` 默认只显示已经被 Git 追踪过的文件变化。Day 3 的主要内容都是新文件，还处于 untracked 状态，所以 `git diff --stat` 不会显示它们。

学习点：

如果想看未追踪文件，要用：

```powershell
git status --short
```

如果想看已经暂存、准备提交的文件，要用：

```powershell
git diff --cached --name-only
```

### 4. 暂存 Day 3 文件

执行命令：

```powershell
git add .
```

作用：把当前所有未被 `.gitignore` 排除的 Day 3 文件加入暂存区。

本次应被暂存的内容包括：

- `data/ecommerce/mock/orders.json`
- `data/ecommerce/mock/products.json`
- `data/ecommerce/docs/faq.md`
- `data/ecommerce/docs/return_policy.md`
- `data/ecommerce/docs/logistics_policy.md`
- `data/ecommerce/docs/warranty_policy.md`
- `app/schemas/document.py`
- `app/pipeline/document_loader.py`
- `app/domains/ecommerce/adapter.py`
- `tests/test_document_loader.py`
- `.learnings/day3_document_loader_learning_notes.md`
- `.learnings/git_learning_notes.md`

### 5. 提交前检查暂存区

执行命令：

```powershell
git diff --cached --name-only
```

作用：列出即将进入 commit 的文件。

学习点：

这是 `git commit` 前非常值得养成的习惯。尤其是本项目有 `.venv/`、pytest cache、学习笔记和源码混在一起时，提交前点名可以避免误提交。

### 6. 创建 Day 3 commit

执行命令：

```powershell
git commit -m "feat: add ecommerce documents and loader"
```

这条命令会把暂存区内容保存成新的 Git 历史版本。

commit message 的含义：

- `feat`：新增功能
- `add ecommerce documents and loader`：这次新增了电商 demo 文档和文档加载器

为什么用 `feat`？

因为 Day 3 新增了项目能力：数据文件、统一 Document schema、通用 document loader 和 ecommerce adapter。它不是单纯的文档更新。

### 7. 推送到 GitHub

执行命令：

```powershell
git push
```

作用：把 Day 3 commit 推送到 GitHub。

因为 Day 1 已经建立了本地 `main` 和远程 `origin/main` 的 tracking 关系，所以这里不用写完整的：

```powershell
git push origin main
```

直接 `git push` 就可以。

### 8. 推送后检查

执行命令：

```powershell
git status --short
git log --oneline --decorate -n 5
```

作用：

- 确认没有未提交内容
- 确认最新 commit 同时出现在 `HEAD -> main` 和 `origin/main`

如果 `git status --short` 没有输出，表示工作区干净。

### 本次 Git 学习点

### `git status` 比 `git diff` 更适合看全局状态

Day 3 主要是新增文件，所以 `git diff --stat` 没输出。

这说明：

- `git diff` 适合看已追踪文件的修改
- `git status` 适合看整体状态，包括未追踪文件

### 新目录不会自动进入 Git

Git 不会“自动追踪目录”。它只追踪文件。

所以新建了：

```text
data/
app/pipeline/
app/domains/
```

这些目录下有文件后，执行 `git add .` 才会把里面的文件加入 Git。

### 每天一个主题 commit 更清晰

Day 1 commit 是 FastAPI 骨架。

Day 2 commit 是 `/chat` API 契约。

Day 3 commit 是数据和 loader。

这种节奏比把多天内容堆成一个大 commit 更容易 review，也更适合你之后复盘项目成长路径。

## 2026-06-04：Day 4 提交 chunking、keyword fallback index 和 retriever

### 本次 Git 目标

Day 4 已完成并通过测试，本次 Git 操作的目标是：

1. 提交 `Chunk` schema、chunker、keyword fallback embedder、in-memory index、retriever。
2. 提交 `tests/test_retriever.py` 和 `experiments/README.md`。
3. 提交 Day 4 学习笔记。
4. 推送到 GitHub。
5. 推送完成后继续开始 Day 5。

### 1. 查看工作区状态

执行命令：

```powershell
git status --short
```

本次看到：

```text
 M app/schemas/document.py
?? .learnings/day4_retrieval_fallback_learning_notes.md
?? app/pipeline/chunker.py
?? app/pipeline/embedder.py
?? app/pipeline/retriever.py
?? app/pipeline/vector_store.py
?? experiments/
?? tests/test_retriever.py
```

含义：

- `M app/schemas/document.py`：已有文件被修改，新增了 `Chunk`。
- `??`：Day 4 新增文件或目录，Git 还没有追踪。

### 2. 查看最近提交

执行命令：

```powershell
git log --oneline --decorate -n 5
```

本次看到最新提交是：

```text
8a0c441 (HEAD -> main, origin/main, origin/HEAD) feat: add ecommerce documents and loader
```

说明本地和远程都停在 Day 3 commit，Day 4 还没有提交。

### 3. 查看已追踪文件的 diff 统计

执行命令：

```powershell
git diff --stat
```

本次只看到：

```text
app/schemas/document.py | 8 ++++++++
```

这是因为 `git diff --stat` 默认只显示 Git 已经追踪过的文件修改。Day 4 大部分是新文件，所以还要结合 `git status --short` 看完整状态。

### 4. 暂存 Day 4 文件

执行命令：

```powershell
git add .
```

作用：把 Day 4 的新增文件、修改文件和更新后的学习文档都放入暂存区。

本次应进入暂存区的主要文件：

- `app/schemas/document.py`
- `app/pipeline/chunker.py`
- `app/pipeline/embedder.py`
- `app/pipeline/vector_store.py`
- `app/pipeline/retriever.py`
- `tests/test_retriever.py`
- `experiments/README.md`
- `.learnings/day4_retrieval_fallback_learning_notes.md`
- `.learnings/git_learning_notes.md`
- `.learnings/ERRORS.md`

### 5. 提交前检查暂存区

执行命令：

```powershell
git diff --cached --name-only
```

作用：确认下一次 commit 会包含哪些文件。

学习点：

Day 4 新增了多个 pipeline 模块，提交前点名尤其重要，能确认没有把 pytest cache、`.venv` 或无关文件带进去。

### 6. 创建 Day 4 commit

执行命令：

```powershell
git commit -m "feat: add chunking and keyword retrieval fallback"
```

commit message 含义：

- `feat`：新增项目能力。
- `add chunking and keyword retrieval fallback`：新增文档切分和 keyword fallback 检索。

为什么不用 “vector search”？

因为 Day 4 主线不是一套真实 semantic vector search，而是 deterministic keyword fallback。commit message 应该诚实表达当前能力。

### 7. 推送到 GitHub

执行命令：

```powershell
git push
```

作用：把 Day 4 commit 上传到 GitHub 的 `origin/main`。

### 本次 Git 学习点

### commit message 不要夸大实现

Day 4 的检索是 keyword fallback，不是真正 embedding API 或向量数据库。所以 commit message 使用：

```text
keyword retrieval fallback
```

这比写成 “add vector search” 更准确。

### 已追踪修改和未追踪文件要一起看

这次 `git diff --stat` 只显示 `document.py`，但 `git status --short` 显示了所有 Day 4 新文件。

所以提交前常用组合是：

```powershell
git status --short
git diff --stat
git diff --cached --name-only
```

它们分别回答：

- 当前有哪些改动？
- 已追踪文件改了多少？
- 即将提交哪些文件？

## 2026-06-04：Day 5 提交 naive RAG pipeline

### 本次 Git 目标

Day 5 已完成并通过测试，本次 Git 操作的目标是：

1. 提交 `prompt_builder.py`、`answer_generator.py`、`rag_pipeline.py`。
2. 提交 `/chat` 从 mock 接到 RAG pipeline 的路由修改。
3. 提交 Day 5 的 RAG pipeline 测试、failure cases 文档和学习笔记。
4. 推送到 GitHub。
5. 推送后继续进入 Day 6。

### 1. 查看工作区状态

执行命令：

```powershell
git status --short
```

本次看到：

```text
 M app/api/routes.py
 M docs/contracts/query_api.md
 M tests/test_chat_contract.py
?? .learnings/day5_naive_rag_pipeline_learning_notes.md
?? app/pipeline/answer_generator.py
?? app/pipeline/prompt_builder.py
?? app/pipeline/rag_pipeline.py
?? docs/failure_cases.md
?? tests/test_rag_pipeline.py
```

含义：

- `M` 表示已有文件被修改。
- `??` 表示新文件还没有被 Git 追踪。

这次既有已有文件修改，也有新文件。提交前需要同时看 `git status --short` 和 `git diff --stat`。

### 2. 查看最近提交

执行命令：

```powershell
git log --oneline --decorate -n 6
```

本次最新提交是：

```text
b719401 (HEAD -> main, origin/main, origin/HEAD) feat: add chunking and keyword retrieval fallback
```

说明本地和远程都停在 Day 4，Day 5 还未提交。

### 3. 查看已追踪文件变化统计

执行命令：

```powershell
git diff --stat
```

本次看到：

```text
app/api/routes.py           | 26 +++++++++++++++-----------
docs/contracts/query_api.md | 44 ++++++++++++++++++++++++++++----------------
tests/test_chat_contract.py |  9 ++++-----
```

这说明 Day 5 修改了 3 个已追踪文件。

但注意：新文件不会出现在这个统计里，所以仍然要看 `git status --short`。

### 4. 暂存 Day 5 文件

执行命令：

```powershell
git add .
```

作用：把 Day 5 的所有候选实现、文档、测试和学习笔记放入暂存区。

本次应进入暂存区的主要文件：

- `app/pipeline/prompt_builder.py`
- `app/pipeline/answer_generator.py`
- `app/pipeline/rag_pipeline.py`
- `app/api/routes.py`
- `docs/contracts/query_api.md`
- `docs/failure_cases.md`
- `tests/test_chat_contract.py`
- `tests/test_rag_pipeline.py`
- `.learnings/day5_naive_rag_pipeline_learning_notes.md`
- `.learnings/git_learning_notes.md`

### 5. 提交前检查暂存区

执行命令：

```powershell
git diff --cached --name-only
```

作用：确认下一次 commit 会包含哪些文件。

Day 5 涉及 API 行为变化，所以提交前点名很重要：要确认测试和契约文档也一起进入 commit，避免代码已经改成 RAG pipeline，但文档还停留在 mock 时代。

### 6. 创建 Day 5 commit

执行命令：

```powershell
git commit -m "feat: connect chat endpoint to naive rag pipeline"
```

commit message 含义：

- `feat`：新增功能。
- `connect chat endpoint to naive rag pipeline`：把 `/chat` 接入 naive RAG pipeline。

为什么写 `naive rag pipeline`？

因为 Day 5 仍然是 Week 1 v0：keyword fallback、rule-based answer generator，不是真实 LLM + production retrieval。

### 7. 推送到 GitHub

执行命令：

```powershell
git push
```

作用：把 Day 5 commit 上传到 GitHub。

### 本次 Git 学习点

### 行为变化要连同测试和文档一起提交

Day 5 把 `/chat` 从 mock 改成 RAG pipeline。如果只提交代码，不提交测试和契约文档，reviewer 会不知道接口行为已经改变。

所以这类 commit 应该包含：

- 代码实现
- 测试更新
- 契约文档更新
- failure cases 或风险说明

### commit message 要说明用户可见的变化

这次不是简单 “add files”，而是 `/chat` endpoint 的行为发生变化。

所以 commit message 直接写：

```text
connect chat endpoint to naive rag pipeline
```

这样以后看 git log，就能清楚知道哪一天 `/chat` 真正接入了 RAG v0。

## 2026-06-04：Day 6 提交 Docker、logging 和工程文档

### 本次 Git 目标

Day 6 已完成并通过本地测试，本次 Git 操作的目标是：

1. 提交 Dockerfile 和 `.dockerignore`。
2. 提交 logging 配置和 RAG pipeline stage 日志。
3. 提交 architecture 文档和 AI development workflow 文档。
4. 提交 README 的 Week 1 当前状态更新。
5. 提交 Day 6 学习笔记和 Docker build 环境问题记录。
6. 推送到 GitHub。

### 1. 查看工作区状态

执行命令：

```powershell
git status --short
```

本次看到：

```text
 M .env.example
 M .learnings/ERRORS.md
 M Dockerfile
 M README.md
 M app/core/config.py
 M app/main.py
 M app/pipeline/rag_pipeline.py
?? .dockerignore
?? .learnings/day6_docker_logging_docs_learning_notes.md
?? app/core/logging_config.py
?? docs/ai-development-workflow.md
?? docs/design/
```

含义：

- `M` 表示已有文件被修改。
- `??` 表示新增文件或目录。

Day 6 既有运行代码变化，也有文档变化，所以提交前要确认两类文件都纳入 commit。

### 2. 查看最近提交

执行命令：

```powershell
git log --oneline --decorate -n 6
```

本次最新提交是：

```text
1cab260 (HEAD -> main, origin/main, origin/HEAD) feat: connect chat endpoint to naive rag pipeline
```

说明本地和远程都停在 Day 5 commit，Day 6 还未提交。

### 3. 查看已追踪文件变化统计

执行命令：

```powershell
git diff --stat
```

本次看到：

```text
.env.example                 |   1 +
.learnings/ERRORS.md         |  42 +++++++++++++++++
Dockerfile                   |   1 +
README.md                    | 104 ++++++++++++++++++++++++++++++++++++++-----
app/core/config.py           |   1 +
app/main.py                  |  11 +++++
app/pipeline/rag_pipeline.py |  28 ++++++++++++
```

这个统计只展示已追踪文件。Day 6 的新文件，比如 `.dockerignore` 和 architecture 文档，还需要通过 `git status --short` 查看。

### 4. 暂存 Day 6 文件

执行命令：

```powershell
git add .
```

作用：把 Day 6 的代码、文档、学习笔记和错误记录全部加入暂存区。

本次应进入暂存区的主要文件：

- `Dockerfile`
- `.dockerignore`
- `.env.example`
- `app/core/logging_config.py`
- `app/core/config.py`
- `app/main.py`
- `app/pipeline/rag_pipeline.py`
- `docs/design/architecture.md`
- `docs/ai-development-workflow.md`
- `README.md`
- `.learnings/day6_docker_logging_docs_learning_notes.md`
- `.learnings/ERRORS.md`
- `.learnings/git_learning_notes.md`

### 5. 提交前检查暂存区

执行命令：

```powershell
git diff --cached --name-only
```

作用：确认下一次 commit 会包含哪些文件。

Day 6 是工程化提交，容易漏掉 `.dockerignore` 或文档文件，所以提交前点名很重要。

### 6. 创建 Day 6 commit

执行命令：

```powershell
git commit -m "chore: add docker logging and architecture docs"
```

commit message 含义：

- `chore`：工程配置、文档和基础设施改进。
- `add docker logging and architecture docs`：本次主要新增 Docker、logging 和架构文档。

为什么这次用 `chore` 而不是 `feat`？

Day 6 没有新增用户可见业务能力，主要是工程可复现、可解释、可维护性建设，所以 `chore` 更合适。

### 7. 推送到 GitHub

执行命令：

```powershell
git push
```

作用：把 Day 6 commit 上传到 GitHub。

### 本次 Git 学习点

### 环境验收失败不一定阻止提交

Day 6 的 Docker build 因为 Docker Desktop daemon 不可用而失败：

```text
failed to connect to the docker API ... dockerDesktopLinuxEngine
```

这类问题已经记录到 `.learnings/ERRORS.md`，并且本地 pytest 与 HTTP 验收通过。

所以可以提交当前代码和文档，同时在 review/后续验收中明确说明 Docker build 还需要在 Docker Desktop 启动后重跑。

关键是：不要隐藏失败，也不要把未验证的 Docker build 说成已通过。

### `chore` commit 也很重要

不是所有 commit 都必须是功能开发。

Docker、logging、README、architecture 文档这类工作，属于项目能否被别人复现和理解的关键工程资产。

这类提交适合用：

```text
chore: ...
docs: ...
```

具体用哪个取决于变化重点。Day 6 同时有 Docker/logging 和文档，所以使用 `chore`。
