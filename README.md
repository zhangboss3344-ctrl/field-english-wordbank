# Field English 专业词库

Field English 的公开词库数据源。Android 客户端可通过 HTTPS 读取 `manifest.json`，检测词库版本并下载 CSV。

## 云端地址

- 版本清单： https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/manifest.json
- 词库 CSV： https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/field_english_words.csv

## 首发内容

- 版本：`1.0.0`（version_code: `1`）
- 词条：125 条
- 格式：UTF-8 CSV
- 字段：`index,英文,中文,分类,备注`
- 覆盖：路由协议、MPLS/SRv6、EVPN/VXLAN、交换与 QoS、光传输、故障处理、工程割接、工程建设、数据中心、现场沟通。

## 客户端更新约定

1. 启动或用户手动刷新时，请求 `manifest.json`。
2. 比较本地保存的 `version_code` 与清单中的 `version_code`；只有远端版本更高时才下载。
3. 从清单的 `file.url` 下载 CSV 到临时文件。
4. 下载完成后校验文件字节数和 SHA-256。
5. 校验通过后解析 CSV，并在数据库事务中替换词库数据。
6. 成功后保存版本号；失败时保留本地上一次有效词库，确保离线可用。

## 数据兼容规则

- CSV 表头固定为 `index,英文,中文,分类,备注`，不要随意改名或调整顺序。
- `index` 是词条稳定 ID。已发布词条不得重新编号；新增词条追加新 ID。
- 更新词库时，客户端应按稳定 ID 关联收藏和学习进度，不要因整表刷新清空用户数据。
- 每次发布词库更新，都必须递增 `version_code`、更新 `version` 和 `updated_at`，并同步更新 CSV 的 SHA-256、字节数和词条数。

## 重要说明

本仓库提供云端数据和更新协议。它不会自动修改已经安装的 APK；Android 工程仍需实现上述清单检查、下载、校验和本地数据替换逻辑，并将清单地址配置为默认更新源。
