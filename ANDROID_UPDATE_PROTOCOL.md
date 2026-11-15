# Android 客户端远程词库更新协议

## 固定入口

`https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/manifest.json`

## 当前客户端限制

- 单个 CSV 最大 8 MiB。
- 解析器最多 20,000 行（包含表头）。
- manifest 中 count 为有效词条数，不包含表头。
- 当前 V1.3.1 客户端识别固定 CSV 表头：`index,英文,中文,分类,备注`。

## 请求流程

1. Android 客户端使用 HTTPS GET 获取 manifest.json。
2. 解析 `version_code`、`content.url`、`content.size_bytes`、`content.sha256`、`content.count`。
3. 若远端 `version_code` 小于或等于本地版本，停止下载。
4. 下载 CSV 至应用私有目录中的临时文件，不要直接覆盖当前词库。
5. 校验实际字节数与 `content.size_bytes` 一致。
6. 计算临时文件 SHA-256，与 `content.sha256` 比较（十六进制小写）。
7. 使用 UTF-8 解码并解析 CSV；确认表头完全匹配，记录数等于 `content.count`，且没有无效或重复英文词条。
8. 校验全部通过后，将云端词条合并到本地词库。
9. 合并成功后再保存本地 `version_code`；删除临时文件。
10. 任一步失败，删除临时文件并保留此前有效的本地词库与版本号。

## 数据库与学习记录

- 当前 V1.3.1 客户端以标准化后的英文词条作为合并键：NFKC 规范化、去除首尾空格、连续空格折叠、忽略大小写。
- CSV 的 `index` 是数据导出序号，不是客户端收藏或学习进度的关联主键。
- 云端更新通过本地词库 Store 合并词条；同名英文词条更新释义，不应清空其他本地导入词汇。
- 收藏、学习进度、错词记录等用户数据必须独立保存，不因云端词库更新而清除。
- 不要把词库下载失败当作应用启动失败；继续使用本地缓存。

## HTTP 建议

- 设置连接与读取超时。
- 支持合理的重试和指数退避。
- 对 manifest 和 CSV 响应检查 HTTP 状态码。
- 可以使用 ETag / Last-Modified 减少重复下载，但版本号仍是业务版本依据。
- manifest 缓存可设置较短有效期；不要长期缓存导致漏掉版本更新。

## 数据发布约束

- 词条 CSV 表头固定为 `index,英文,中文,分类,备注`。
- 发布前必须检查文件大小、行数、英文词条唯一性、UTF-8 解码和 SHA-256。
- 每次内容变化都递增 `version_code`，更新 `version`、`updated_at`、词条数、文件大小和 SHA-256。
- 不同开放数据源按各自许可证保留来源说明，不要在没有核验许可的情况下混合再发布。
