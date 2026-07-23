# 中国政府采购网(`http://www.ccgp.gov.cn`)招标公告分析推送系统

## 项目概述
自动抓取中国政府采购网招标公告，经 LLM 大模型分析筛选后，将相关项目通过邮件推送并保存为 Excel。

系统采用模块化设计，包含四大核心模块：**检索 → 分析 → 推送 → 存储**。

---

## 文件结构
```
project/
├── main.py                     # 入口文件
├── config.yaml                 # 配置文件
├── .env                        # 环境变量 (LLM / SMTP 密钥，不提交到版本库)
├── requirements.txt            # 依赖清单
├── Makefile                    # 常用命令
├── prompts/
│   └── tender_analysis.md      # LLM 提示词与关键词
└── src/
    ├── config.py               # 配置加载器 (YAML + .env)
    ├── models.py               # 数据模型 (TenderItem / AnalysisResult)
    ├── pipeline.py             # 主流程编排
    ├── crawlers/               # 检索模块
    │   ├── base.py             # 爬虫基类
    │   └── ccgp_crawler.py     # 政府采购网爬虫
    ├── analyzers/              # 分析模块
    │   ├── base.py             # 分析器基类
    │   └── llm_analyzer.py     # LangChain + LLM 分析器
    ├── notifiers/             # 推送模块
    │   ├── base.py             # 通知器基类
    │   └── email_notifier.py   # 邮件通知器
    └── utils/                 # 工具
        ├── http.py             # HTTP 请求 (随机 UA + 编码检测)
        └── excel.py            # Excel 输出
```

---

## 模块说明

### 1. 检索模块 (`src/crawlers/`)
- 抓取公告列表，支持关键词、区域、时间范围过滤
- 抓取公告详情页正文内容
- 随机 User-Agent + 请求延迟，规避反爬
- `BaseCrawler` 基类便于扩展其他站点

### 2. 分析模块 (`src/analyzers/`)
- 从 Markdown 文件加载提示词与关键词
- 调用 LLM (OpenAI 兼容接口) 判断公告相关性
- 容错解析 LLM 返回的 JSON 结果
- `BaseAnalyzer` 基类便于扩展其他分析器

### 3. 推送模块 (`src/notifiers/`)
- 生成带样式的 HTML 表格邮件
- 支持 SMTP / SMTP_SSL
- `BaseNotifier` 基类便于扩展其他通知渠道

### 4. 存储模块 (`src/utils/excel.py`)
- 将相关项目保存为带时间戳的 Excel 文件
- 文件命名格式：`filtered_data_YYYYMMDD_HHMMSS.xlsx`

---

## 快速开始

### 1. 安装依赖
```bash
make install
# 或
pip install -r requirements.txt
```

### 2. 配置
编辑 `config.yaml` 调整抓取参数与分析设置：
```yaml
crawler:
  days_back: 1        # 抓取最近几天
  max_pages: 50       # 最大页数
  kw: "桥梁"           # 搜索关键词
  fetch_detail: true   # 是否抓取详情页
```

在 `.env` 中填写密钥：
```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-llm-endpoint/v1
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SENDER_EMAIL=you@example.com
SENDER_PASSWORD=your-password
RECEIVER_EMAIL=you@example.com
```

### 3. 运行
```bash
make run
# 或
python main.py
```

### 4. 自定义关键词与提示词
编辑 `prompts/tender_analysis.md`，按 `## keywords` / `## system_prompt` / `## user_prompt_template` 分段。

---

## 输出文件
- Excel：`filtered_data_YYYYMMDD_HHMMSS.xlsx`
- 邮件：发送至 `.env` 中配置的收件邮箱

清理生成的 Excel：
```bash
make clean
```

---

## 注意事项
1. 遵守 robots.txt 协议，控制爬取频率
2. 每日运行次数建议不超过 3 次
3. 若需长期运行，建议设置定时任务(如 crontab)
4. 本程序仅供个人学习、研究和技术实验使用，不得用于商业目的或违反法律法规的行为
5. 使用者应自行承担因爬取数据而产生的所有法律责任，程序开发者不承担责任
