# PII-Bench：面向查询感知隐私保护系统的评估基准（ACL 2026）

**[English](README.md)** | 中文

本仓库为 ACL 2026 论文官方数据集与评测代码仓库：
> **PII-Bench: Evaluating Query-Aware Privacy Protection Systems**
> 沈豪（Hao Shen）、顾周洪（Zhouhong Gu）、洪浩凯（HaoKai Hong）、韩伟力\*（Weili Han）、柴洪峰（Hongfeng Chai）
> *复旦大学金融科技研究院 & 复旦大学数据分析与安全实验室*

**官方数据集镜像：**
- **HuggingFace：** https://huggingface.co/datasets/shenhao/PII-Bench
- **ModelScope（魔搭社区）：** https://modelscope.cn/datasets/shenhao23/PII-Bench

> **持续迭代更新说明：** 本数据集处于持续维护状态，**后续将不断迭代更新**（包括但不限于未来补充扩展子集与进一步质量优化）。`data/paper_exact/` 目录（及 HuggingFace / ModelScope 的 `paper_exact` 配置）将永久冻结，以保证 ACL 2026 论文全部实验结果 **0.0000** 零误差可复现。

---

## 项目简介

用户在使用大语言模型（LLM）时，常会在提示词中暴露大量个人身份信息（PII）。“完全不脱敏”会带来隐私泄露风险，而“全部脱敏”又会严重破坏模型回答质量。

为此，**PII-Bench** 提出**查询无关 PII 脱敏（Query-Unrelated PII Masking）**策略，并构建了包含 **2,842 条核心测试样本**、覆盖 **7 大 PII 类别**（`PER`、`CODE`、`LOC`、`ORG`、`DEM`、`DATETIME`、`QUANTITY`）与细粒度子类的综合基准，系统评测三大核心任务：

1. **任务 1 — PII 识别（PII Detection）**：识别文本中所有 PII 实体的最小片段 $E$、归属主体 $s \in S$ 及其 PII 类型 $t \in T$。
2. **任务 2 — 查询相关 PII 识别（Query-Related PII Detection）**：判断回答用户问题 $q$ 所必需的最小 PII 子集 $E_q \subseteq E$。
3. **任务 3 — 查询无关 PII 脱敏（Query-Unrelated PII Masking）**：仅脱敏与查询无关的 PII（$E \setminus E_q$），保留关键信息 $E_q$ 以兼顾隐私保护与可用性。

---

## 数据版本说明（`cleaned` / HF & MS `default` 与 `paper_exact` 的关系）

> **命名说明**：GitHub 仓库中的 **`data/cleaned/`** 与 HuggingFace / ModelScope 中的 **`default` 配置** 数据内容 **100% 完全一致**（逐行验证完全相同），区别仅在于平台命名习惯——HuggingFace / ModelScope 默认配置名为 `default` 以支持 `load_dataset("shenhao/PII-Bench")` 直接加载。

- **`data/cleaned/`（推荐，对应 HuggingFace / ModelScope `default` & `privacy_utility` 配置）**：清洗并规范化后的 **v1.1** 正式发布版。共修复 474 项已审计缺陷：移除 `PII_hard` 残留的 `predict` 字段、清除幽灵实体与 4 个 `UNKNOWN` 类型、对齐全部数组长度、修复 1 处粗粒度错标（`Christian`: `ORG → DEM`）、恢复全部 1,221 组同描述双查询的 100% 实体对称性、去除实体首尾空格、清理同主体重复实体、规范 8 个极少数异名子标签，并用 span 安全的脱敏算法重算 `pii_masked_200.jsonl`（彻底修复 3 条误脱敏查询相关 PII 与 89+63 处大小写漏脱敏）。经论文原模型预测实测，核心评测指标波动 $\le +0.0015$ F1 且模型排名 100% 不变。
- **`data/paper_exact/`（永久冻结，对应 HuggingFace / ModelScope `paper_exact` 配置）**：与 ACL 2026 论文实验逐字一致的原始标注（仅移除 `PII_hard.jsonl` 中意外残留的模型输出字段 `predict`，并原样保留 `PII_masked.jsonl`），可 100% 零误差复现论文 Table 3、Table 10 及所有实验表格。

详细清洗变更与逐项指标对比见 [CHANGELOG_DATA_CLEANING.md](CHANGELOG_DATA_CLEANING.md)。

---

## 数据集统计

| 数据子集 | 样本数 | 独立描述数 | 平均主体数 | 描述平均字符数 | 平均 PII 数 | 查询平均字符数 | 查询相关 PII 数 | 实体总数（`cleaned` v1.1 / `paper_exact` Table 10） |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **PII-Single** | 1,214 | 607 | 1.00 | 893.48 | 7.66 / 7.67 | 211.21 | 1.95 | 9,300 / 9,303 |
| **PII-Multi** | 1,228 | 614 | 2.00 | 652.65 | 13.14 | 236.21 | 2.06 | 16,136 / 16,136 |
| **PII-Hard**\* | 200 | 200 | 1.43 | 746.08 | 9.18 / 9.17 | 222.66 | 2.06 | 1,835 / 1,834 |
| **PII-Distract** | 200 | 200 | 7.47 | 4,403.64 | 51.05 / 51.08 | 859.68 / 859.69 | 5.82 | 10,210 / 10,211 |
| **总计** | **2,842** | **1,421** | **1.92** | **1,026.07** | **13.19** | **268.45** | **2.28** | **37,481 / 37,484** |

\* `PII-Hard` 是从 `PII-Single`（114 条）和 `PII-Multi`（86 条）中抽取的困难子集，索引映射见 `data/paper_exact/hard_samples_line_numbers.json`。

---

## 快速开始

```bash
# 1. 安装依赖并校验本地数据完整性
pip install -r requirements.txt
python eval/verify_dataset.py

# 2. 通过环境变量配置 OpenAI 兼容接口（勿在代码中硬编码密钥）
export OPENAI_API_KEY="your-api-key"
# export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"

# 3. 运行任务 1：PII 识别
python -m eval.run_eval \
  --data data/cleaned/pii_single.jsonl \
  --task detection \
  --model gpt-4o \
  --output outputs/det_single_gpt4o.jsonl

# 4. 运行任务 2：查询相关 PII 识别
python -m eval.run_eval \
  --data data/cleaned/pii_single.jsonl \
  --task query_related \
  --prompt cot \
  --model gpt-4o \
  --output outputs/qrel_cot_single_gpt4o.jsonl

# 5. 聚合任务 3：查询无关 PII 脱敏指标
python -m eval.aggregate_results \
  --task masking \
  --pred outputs/qrel_cot_single_gpt4o.jsonl \
  --recog-pred outputs/det_single_gpt4o.jsonl \
  --dataset data/cleaned/pii_single.jsonl
```

如需复现原始脚本使用的合并文件 `PII_final.jsonl`（`PII_multi + PII_single` 共 2,442 条）：
```bash
python scripts/build_pii_final.py --variant paper_exact
```

---

## 真实性保留与维护说明

- 核心 2,842 条合成样本刻意保留真实场景格式（如常见邮箱后缀 `@163.com`、`@gmail.com` 以及中文车牌 `湘A-65225`、`黑A53975`、`鄂A·55978` 等），以贴近真实隐私保护评测需求。
- 本数据集将持续迭代更新，欢迎通过 GitHub Issues 反馈问题或建议。

## 引用

```bibtex
@inproceedings{shen2026piibench,
  title     = {{PII-Bench}: Evaluating Query-Aware Privacy Protection Systems},
  author    = {Shen, Hao and Gu, Zhouhong and Hong, HaoKai and Han, Weili and Chai, Hongfeng},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (ACL 2026)},
  year      = {2026}
}
```
