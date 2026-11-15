# Android 客户端远程词库更新协议

## 固定入口

`https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/manifest.json`

## 请求流程

1. Android 客户端使用 HTTPS GET 获取 manifest.json。
2. 解析 `version_code`、`content.url`、`content.size_bytes`、`content.sha256`、`content.count`。
3. 若远端 `version_code` 小于或等于本地版本，停止下载。
4. 下载 CSV 至应用私有目录中的临时文件，不要直接覆盖当前词库。
5. 校验实际字节数与 `content.size_bytes` 一致。
6. 计算临时文件 SHA-256，与 `content.sha256` 比较（十六进制小写）。
7. 使用 UTF-8 解码并解析 CSV；确认表头完全匹配，记录数等于 `content.count`，且 index 不重复。
8. 校验全部通过后，在数据库事务中更新词库。
9. 事务成功后再保存本地 `version_code`；删除临时文件。
10. 任一步失败，删除临时文件并保留旧词库与旧版本号。

## 数据库与学习记录

- 词条以 CSV 的 `index` 作为稳定主键。
- 收藏、学习进度、错词记录等用户数据应独立于词库内容存储。
- 更新词库时按稳定主键 upsert；删除词条也不要级联删除用户学习历史。
- 不要把词库下载失败当作应用启动失败；继续使用本地缓存。

## HTTP 建议

- 设置连接与读取超时。
- 支持合理的重试和指数退避。
- 对 manifest 和 CSV 响应检查 HTTP 状态码。
- 可以使用 ETag / Last-Modified 减少重复下载，但版本号仍是业务版本依据。
- manifest 缓存可设置较短有效期；不要长期缓存导致漏掉版本更新。

## 当前发布

- version: `1.0.0`
- version_code: `1`
- entries: `125`
- CSV: `field_english_words.csv`

## 后续发布约束

每次发布都递增 version_code，并更新 version、updated_at、词条数、文件大小和 SHA-256。不要复用已发布版本号。
