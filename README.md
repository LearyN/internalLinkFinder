Internal Link Finder

一个用于发现网站内部链接机会的桌面工具。它基于 TF-IDF 和余弦相似度分析页面内容，为每个页面推荐相关性最高的内部链接候选。

使用步骤
步骤 1：使用 Screaming Frog 提取页面内容

打开 Screaming Frog，爬取需要分析的页面。

找到包含正文的页面，右键 → 检查，复制目标文本块的 XPath。

在 Screaming Frog 中设置 自定义提取，粘贴 XPath 并运行爬网。

爬网完成后，导出结果为 CSV 文件，并确保：

文件命名为 custom_extraction_full_text.csv（或其他名称也行）。

列结构至少包含：

address

status code

status

content（提取的正文，确保去掉空行）

特别注意：content 列名必须准确。

步骤 2：运行 Internal Link Finder

下载或复制本项目代码，并使用提供的 exe 工具：

文件路径：dist/InternalLinkFinder.exe

双击即可启动 GUI。

在 GUI 界面中：

点击 Browse，选择导出的 CSV 或 Excel 文件。

确认 URL 列为 address，内容列为 content（大小写不敏感）。

设置相似度阈值（默认 0.6）和每页推荐的 Top N 链接数量（默认 10）。

点击 Run 开始分析。

分析完成后，日志窗口会显示生成的链接机会总数。

步骤 3：保存结果

点击 Save Results，选择保存路径。

工具会输出一个 CSV 文件，结构如下：

source_url：源页面

candidate_url：推荐的内部链接目标

similarity_score：相似度分数（0~1）
