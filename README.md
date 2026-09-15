# 《机器学习理论与实践》交互平台

本仓库负责课程大作业的 Web 交互平台：Vue 3 前端、FastAPI interaction layer，以及与独立 ML 仓库之间的稳定集成边界。模型算法、训练、数据处理和评价仍由 [26MLP_team07](https://github.com/Icey18899877399/26MLP_team07) 独立维护，本仓库不会复制一套 ML Core。

## 双仓库关系

```text
Vue 3 --HTTP/JSON--> FastAPI --Python API--> ml_core --internal--> Models
```

ML 源码以 Git submodule 位于 `external/ml-core`。Submodule 保留独立历史并让本仓库只记录一个 commit pointer；运行时边界则是未来可安装的 Python package `ml_core`。详见 [架构说明](docs/ARCHITECTURE.md) 和 [ML 集成合同](docs/ML_INTEGRATION_CONTRACT.md)。

## 获取代码

新 clone：

```powershell
git clone --recurse-submodules <interaction-repo-url>
cd 15a-machine-practice
```

已经 clone 但尚未获取 submodule：

```powershell
git submodule update --init --recursive
```

## Backend

需要 Python 3.11+：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python -m uvicorn backend.main:app --reload
```

服务默认位于 `http://127.0.0.1:8000`，OpenAPI 文档位于 `/docs`。当前端点：

- `GET /api/health`
- `GET /api/models`
- `GET /api/datasets`
- `POST /api/experiments`

## ML package

当前 pinned ML commit 还没有 packaging metadata 或 `ml_core` 公共入口，因此目前不要执行 editable install，也没有真实 ML 实验接入。ML 仓库负责人实现合同后，安装方式应为：

```powershell
python -m pip install -e external/ml-core
```

随后重启 FastAPI。`/api/health` 应从 `available: false` 变为 `available: true`。FastAPI 不会回退到 `Models.*` 私有 import。

## Frontend

需要 Node.js 20+ 与 pnpm：

```powershell
pnpm --dir frontend install
pnpm --dir frontend dev
```

打开 `http://127.0.0.1:5173`。Vite 会把 `/api` 代理到本地 FastAPI。ML API 不可用时，页面会明确显示“ML 待接入”并禁用真实实验入口，不生成 mock 结果。

生产构建：

```powershell
pnpm --dir frontend build
```

## 测试

```powershell
python -m pytest
```

测试中的 `FakeMLBackend` 只验证 HTTP、schema 和依赖倒置；生产应用始终使用 `PackageMLBackend`。在 ML 仓库提供合同前，没有真实 integration smoke test，也不能把测试替身结果称为 ML 实验结果。

## 课程交付提醒

课程要求最终以一个 PDF 附件提交，并在其中提供可访问的代码仓库链接、运行说明、截图与架构设计；代码仓库不得包含数据集本体。当前 ML submodule 所指向的上游 commit 仍跟踪数据集，这是由 ML 仓库负责人在最终交付前处理的已知缺口。
