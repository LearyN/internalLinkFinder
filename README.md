# Internal Link Finder 🔗✨  
一个用于发现网站内部链接机会的桌面工具。  
A desktop tool for discovering **internal link opportunities** on your website.  

它基于 **TF-IDF** 和 **余弦相似度 (Cosine Similarity)** 分析页面内容，为每个页面推荐最相关的内部链接候选。  
It leverages **TF-IDF** and **cosine similarity** to analyze page content and recommend the most relevant internal link candidates.  

---

## 🚀 使用步骤 (Usage Steps)

### 🐸 步骤 1：使用 Screaming Frog 提取页面内容  
**Step 1: Extract page content with Screaming Frog**  

1. 打开 **Screaming Frog**，爬取需要分析的页面。  
   Open **Screaming Frog** and crawl the target pages.  

2. 找到包含正文的页面，右键 → **检查 (Inspect)**，复制目标文本块的 **XPath**。  
   Locate the main content block, right-click → **Inspect**, copy the **XPath**.  

3. 在 Screaming Frog 中设置 **Custom Extraction**，粘贴 XPath 并运行爬网。  
   Configure **Custom Extraction** in Screaming Frog, paste the XPath, and run the crawl.  

4. 导出结果为 CSV，并确保：  
   Export results to a CSV file and ensure:  
   - 文件命名为 `custom_extraction_full_text.csv`（或其他任意名称）  
     Name file as `custom_extraction_full_text.csv` (or any name)  
   - 列结构至少包含 (columns must include):  
     - `address`  
     - `status code`  
     - `status`  
     - `content`（正文内容，去掉空行，列名必须准确）  
       `content` (main text, cleaned, column name must be exactly `content`)  

---

### 💻 步骤 2：运行 Internal Link Finder  
**Step 2: Run Internal Link Finder**  


2. 双击 exe 启动 GUI。  
Double-click the exe to launch the GUI.  

3. 在 GUI 界面中 (In the GUI):  
- 点击 **Browse** → 选择导出的 CSV 或 Excel 文件  
  Click **Browse** → Select exported CSV/Excel file  
- 确认 URL 列为 `address`，内容列为 `content`（大小写不敏感）  
  Ensure URL column = `address`, Content column = `content` (case-insensitive)  
- 设置相似度阈值（默认 0.6）  
  Set similarity threshold (default = 0.6)  
- 设置每页推荐的 Top N（默认 10）  
  Set Top N recommendations per page (default = 10)  
- 点击 **Run** → 开始分析  
  Click **Run** → Start analysis  

4. 分析完成后，日志窗口会显示生成的内部链接机会总数。  
Once complete, the log will display the total number of internal link opportunities generated.  

---

### 💾 步骤 3：保存结果  
**Step 3: Save Results**  

1. 点击 **Save Results**，选择保存路径。  
Click **Save Results**, choose a save path.  

2. 工具会输出一个 CSV 文件，结构如下：  
The tool will output a CSV file with the following structure:  

| source_url (源页面) | candidate_url (候选内部链接) | similarity_score (相似度) |  
|---------------------|-----------------------------|---------------------------|  
| https://.../page1   | https://.../page2           | 0.78                      |  
| https://.../page1   | https://.../page3           | 0.72                      |  

---


