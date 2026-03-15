# 双模型分析配置说明

## 方案：使用 LLM_CHANNELS 实现双模型并行分析

### 步骤 1: Fork 项目

1. 访问 https://github.com/rockyguo2024/daily_stock_analysis
2. 点击右上角 **Fork** 按钮

### 步骤 2: 配置 GitHub Secrets

在你的 Fork 仓库中，添加以下 Secrets：

| Secret 名称 | 值 |
|-------------|-----|
| `GEMINI_API_KEY` | 你的 Google API Key |
| `OPENAI_API_KEY` | `sk-365cf5111f1a4ebc8bfbe87793122b9a` |
| `OPENAI_BASE_URL` | `https://api.deepseek.com/v1` |
| `LLM_CHANNELS` | (见下面JSON) |

### 步骤 3: LLM_CHANNELS 配置

在 Secrets 中添加 `LLM_CHANNELS`，值如下（不要换行）：

```json
{"gemini":{"model":"gemini-2.0-flash"},"deepseek":{"model":"deepseek-chat","api_base":"https://api.deepseek.com/v1","api_key":"sk-365cf5111f1a4ebc8bfbe87793122b9a"}}
```

### 步骤 4: 修改代码支持双模型

**方法 A：简单方案 - 使用环境变量**

在 `.env` 文件中添加：
```
DUAL_MODEL_ENABLED=true
GEMINI_MODEL=gemini-2.0-flash
DEEPSEEK_MODEL=deepseek-chat
```

**方法 B：修改 analyzer.py**

在 `src/analyzer.py` 的 `analyze` 方法中，添加第二个模型的调用并合并结果。

---

## 本地运行

```bash
# 克隆你的 Fork
git clone https://github.com/你的用户名/daily_stock_analysis.git
cd daily_stock_analysis

# 复制环境配置
cp .env.example .env

# 编辑 .env，添加你的 API Keys
vim .env

# 运行分析
python dual_model_analysis.py 002709 天赐材料
```

---

## 输出示例

脚本会输出类似这样的结果：

```
================================================================================
📊 双模型综合分析报告
================================================================================

股票: 天赐材料 
代码: 002709

================================================================================
🟢 Gemini 模型分析结果
================================================================================
[Gemini 的分析内容...]

================================================================================
🔵 DeepSeek 模型分析结果
================================================================================
[DeepSeek 的分析内容...]

================================================================================
📝 综合分析建议
================================================================================

当两个模型的结论一致时，信号更强；
当结论不一致时，建议保持谨慎，等待进一步确认。
```
