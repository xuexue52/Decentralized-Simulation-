# Multi-server_time 实验细节文档

## LLM 相关细节

### 使用的模型和 API

- **模型**: `gpt-4o-mini`
- **API Base URL**: `http://api.tenclock.shop:3000/v1`
- **备选模型列表** (降级策略): `["gpt-4o-mini", "gpt-3.5-turbo"]`
- **API 调用方式**: OpenAI-compatible API (POST `/chat/completions`)

### 生成参数

- **Temperature**: `0.7` (所有 LLM 调用统一使用)
- **Top-p**: 未设置（使用 API 默认值）
- **Max tokens**: 未显式设置（使用 API 默认值），但代码中有 token 限制逻辑：
  - `MAX_TOKEN_COUNT = 10000` (用于截断 prompt)
  - `MAX_DISPLAY_TOKEN_COUNT = 5000` (用于显示)

### System Prompt 和 Safety Filter

- **System Prompt**: 未使用（所有 prompt 都是 user role）
- **Safety Filter**: 未在代码中显式配置（依赖 API 提供商的默认设置）

### 参数统一性

**所有 LLM 调用使用相同的参数配置**：
- 模型: `gpt-4o-mini`
- Temperature: `0.7`
- 所有任务（发帖、环境评估、互动决策、立场调整、反思生成）都使用相同的参数

代码位置：`src/agents/social_agent.py:736-738`

## Feed 和迁移规则

### Time Feed 规则

**具体实现**：
- 从所有服务器获取**最近 3 条**关注者的帖子（`MAX_FOLLOWING_POSTS = 3`）
- 从当前服务器获取**最近 6 条**非关注者的帖子（`MAX_SERVER_POSTS = 6`）
- 按时间戳排序（`timestamp` 字段，ISO 格式）
- 合并后按时间顺序展示：先展示关注者帖子，再展示服务器帖子

代码位置：`src/models/social_network.py:84-114`

**注意**：本项目为 "Multi-server_time"，使用时间排序，**不使用热门排序**。

### 迁移规则

- **迁移阈值**: `satisfaction < 6` (满意度评分 1-10 分，低于 6 分触发迁移)
- **迁移目标**: 随机选择其他可用服务器（排除当前服务器）
- **迁移时机**: 每轮互动后评估环境，如果满意度 < 6 则立即迁移

代码位置：
- 迁移阈值检查：`src/agents/social_agent.py:313`
- 迁移逻辑：`src/agents/social_agent.py:318-349`

## 随机性与复现性

### 实验规模

- **总轮次**: `30 rounds` (`TOTAL_ROUNDS = 30`)
- **Agent 数量**: `50 agents` (从配置文件路径 `Multi-server_time_50agents` 推断)
- **服务器数量**: `3 servers` (A, B, C)


## 代码和配置公开

**当前状态**：
- 代码已存在于 `Multi-server_time/` 目录
- 配置文件：`src/utils/config.py`
- 所有 prompt 模板：`src/utils/prompts.py`

**建议声明**：
> Code and configs will be released upon acceptance.

## 其他重要细节

### Token 使用记录

- 所有 LLM 调用的 token 使用量都记录到 `logs_token_usage.csv`
- 记录字段：`prompt_tokens`, `completion_tokens`, `total_tokens`, `model`, `action_type`

### 重试机制

- **最大重试次数**: 5 次
- **初始延迟**: 2.0 秒
- **退避因子**: 1.8 (指数退避)
- **最大延迟**: 20.0 秒
- **抖动范围**: 0.5x - 1.5x

代码位置：`src/agents/social_agent.py:701-841`

### 记忆管理

- **最大记忆条数**: 100 (`MAX_MEMORY_ITEMS`)
- **反思触发阈值**: 累计重要性分数 ≥ 50
- **反思使用的记忆数**: 最近 20 条 (`MAX_REFLECTION_MEMORIES`)
- **相关记忆数**: 最多 5 条 (`MAX_RELEVANT_MEMORIES`)

---





