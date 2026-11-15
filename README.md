# Field English 开放词库

Field English 的公开词库数据源。Android 客户端通过 HTTPS 读取 `manifest.json`，检测版本并下载 CSV。当前 Android V1.3.1 客户端限制为单个词库最多 20,000 条、CSV 最大 8 MiB，因此云端发布的是筛选后的轻量词库，而不是把数十万条原始数据直接塞进手机。

## 云端地址

- 版本清单：https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/manifest.json
- APP 词库：https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/field_english_words.csv

## 数据组成

1. **Field English 自建专业词库**：数通路由协议、MPLS/SRv6、EVPN/VXLAN、交换与 QoS、光传输、故障处理、工程割接、机房建设、数据中心和现场沟通。
2. **ECDICT 高频英汉词库**：从上游公开数据中按词频、Oxford 标记和考试标签筛选，最多 15,000 条，提供中文释义、音标、词性、英文释义和词形信息。

首发的 125 条自建专业词汇单独保存在 `curated/field_english_professional.csv`。发布文件 `field_english_words.csv` 由脚本生成，不要直接把它当作人工维护源文件。

## 开放数据来源与许可

- ECDICT：https://github.com/skywind3000/ECDICT
- 上游仓库包含 MIT LICENSE；本仓库保留副本于 `licenses/ECDICT-MIT-LICENSE.txt`。
- 上游 README 说明其数据来自多种词表、词典及语料资源。请阅读 `THIRD_PARTY_NOTICES.md`；如用于商业发行或大规模再分发，应进一步核验上游数据的第三方来源和权利。
- 其他候选语料（Tatoeba、Wiktionary/Kaikki、CC-CEDICT）在 `SOURCES.md` 单独记录，尚未合并进当前 CSV，避免混淆不同许可证。

## 自动构建与更新

- 构建脚本：`scripts/build_wordbank.py`
- 自动任务：`.github/workflows/refresh-ecdict.yml`
- 每月从 ECDICT 上游拉取一次，也可以在 GitHub Actions 页面手动运行 **Refresh open English-Chinese dictionary**。
- 脚本会合并自建词库和筛选后的 ECDICT 词条，去重并检查 Android 的 20,000 条 / 8 MiB 限制。
- 内容变化时自动递增 `version_code` 和补丁版本号，更新 CSV 字节数、词条数及 SHA-256。
- GitHub Actions 自动提交更新后的 `field_english_words.csv` 与 `manifest.json`。

## CSV 格式

固定表头：`index,英文,中文,分类,备注`。请保持 UTF-8 编码。

Android V1.3.1 客户端实际按标准化后的英文词条（忽略大小写、合并多余空格）去重和合并；`index` 是导出序号，不是客户端学习记录的关联主键。不要修改客户端现有数据模型的前提下更换表头。

## 本地测试构建脚本

需要 Python 3.10+，并准备一份 ECDICT 原始 CSV：

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/build_wordbank.py --source /path/to/ecdict.csv
```
