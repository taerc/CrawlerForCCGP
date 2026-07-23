# Makefile for CrawlerForCCGP - 招标公告分析推送系统
# Python 3.8+ required

PYTHON := python3
MAIN := main.py

.PHONY: help install run lint clean

help: ## 显示帮助信息
	@echo "CrawlerForCCGP - 招标公告分析推送系统"
	@echo ""
	@echo "可用命令:"
	@echo "  make install        安装项目依赖"
	@echo "  make run            运行主程序 (含 LLM 分析)"
	@echo "  make lint           语法检查所有 Python 文件"
	@echo "  make clean          清理生成的 Excel 文件"

install: ## 安装项目依赖
	$(PYTHON) -m pip install -r requirements.txt

run: ## 运行主程序
	$(PYTHON) $(MAIN)

lint: ## 语法检查所有 Python 文件
	$(PYTHON) -m py_compile $(MAIN) src/config.py src/models.py src/pipeline.py
	$(PYTHON) -m py_compile src/crawlers/base.py src/crawlers/ccgp_crawler.py
	$(PYTHON) -m py_compile src/analyzers/base.py src/analyzers/llm_analyzer.py
	$(PYTHON) -m py_compile src/notifiers/base.py src/notifiers/email_notifier.py
	$(PYTHON) -m py_compile src/utils/http.py src/utils/excel.py

clean: ## 清理生成的 Excel 文件
	rm -f filtered_data_*.xlsx
