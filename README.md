# BestBYD × TrendRadar

比亚迪资讯与国内社媒热榜监控，使用 [TrendRadar](https://github.com/sansan0/TrendRadar) 的完整采集和报告引擎。

在线报告：[BestBYD TrendRadar](https://asher-y-ma.github.io/bestbyd-trendradar/)。

## 运行安排

- GitHub Actions 每小时第 17 分钟采集一次，也可在 Actions 页面手动运行 **Collect BYD trends**。
- 来源：微博、抖音、知乎、B站热搜、百度热搜、今日头条、澎湃新闻、财联社热门。
- 关注比亚迪、腾势、仰望、方程豹和明确的相关车型名称；热榜没有覆盖的帖子不会被发现。
- `data/latest.json` 保存最近 7 天内出现过的相关线索，最多 500 条，保留首次/最近观测时间与原始链接。
- `reports/latest.html` 和在线报告页是 TrendRadar 生成的最新关键词报告。
- 全部采集失败时任务报错，保留上次成功结果；部分平台失败时输出 `degraded`，不会伪装为全源成功。

## 与 BestBYD 的关系

BestBYD 的 Hostinger 后端按小时读取公开 JSON，将热点用于匹配车型/话题并提高有原文证据的新闻选题优先级。热榜标题和排名不作为已核实事实，也不被扩写成没有来源支撑的文章。

本仓库关闭 AI 筛选、AI 翻译、AI 分析和消息通知。AI 写作、校对与发布由 BestBYD 的 WordPress 插件执行，API 密钥仅加密保存在网站服务器，调用时段为北京时间 **21:00 至次日 04:00**。

## 配置与维护

- `config/config.yaml`：平台、时区和 TrendRadar 功能配置。
- `config/frequency_words.txt`：TrendRadar 关键词报告规则。
- `config/topics.json`：导出的车型与话题标签。
- `scripts/export_bestbyd.py`：验证平台域名、筛选相关标题、去重和过期处理。
- `upstream.json`：固定的上游版本和提交。工作流使用同一提交，升级前需重新验证配置与数据库格式。

使用标准 Ubuntu GitHub-hosted runner，没有采购服务器或付费服务。GitHub 的免费政策、调度延迟、仓库不活跃停用规则仍适用。工作流会提交真实采集结果，不添加专门的空提交或签到任务。GitHub 故障、上游热榜接口不可用或平台变更仍可能影响更新。

此仓库公开，代码、配置、采集标题、来源链接、报告和提交历史可被公众查看。不要提交 Cookie、AI 密钥、WordPress 密码或私人联系信息。删除最新 JSON 中的旧条目不会删除 Git 历史。

## 开源说明

TrendRadar 版权属于其原作者与贡献者，原始项目采用 GPL-3.0。本仓库的配置与导出适配同样采用 GPL-3.0，许可证见 [LICENSE](LICENSE)。原始运行代码从固定的上游提交检出，不复制或启用上游的通知配置及试用签到工作流。

热点数据由上游 NewsNow 接口提供；原始内容权利属于各出版者和平台。监控结果仅提供来源线索。
