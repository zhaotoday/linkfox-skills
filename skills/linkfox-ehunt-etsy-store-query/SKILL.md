---
name: linkfox-ehunt-etsy-store-query
description: 通过 EHunt MCP 工具 `_ehunt_storeQuery`（展示名「Etsy店铺查询」）按多维度筛选 Etsy 店铺（销量、收藏、评论、开店时间、国家、主营类目、Raving/星标等）。当用户提到 EHunt Etsy 店铺、Etsy 店搜、Etsy seller、Etsy 店铺排行、Etsy 周销量店铺、ehunt stores、Etsy店铺查询、_ehunt_storeQuery 时触发。即使用户未写 EHunt，只要在 Etsy 上找店铺、筛店铺数据或分析店铺表现，也应触发此技能。
---

# EHunt Etsy 店铺查询（`_ehunt_storeQuery`）

在具备 LinkFox「第三方数据服务」MCP 时，按工具名 **`_ehunt_storeQuery`** 调用（MCP 展示名：**Etsy店铺查询**，以当前环境下发的工具元数据为准）。鉴权与上游路由由网关处理；若响应含根级 `code` 字段，是否成功以实网为准。

## 要点

- **分页**：`page` 从 1 起；`pageSize` 默认 20、最大 100。
- **区间入参**：`begin*` / `end*` 成对对应上游逗号范围；只填一侧时上游为「起始~」或「~结束」。
- **排序**：`sortBy` 仅 **8~11**（8 总销量、9 周销量、10 评论数、11 收藏数）。`sortDesc`：**1=降序，0=升序**（勿与商品接口的 `sortDesc` 混用）。

## 脚本（可选）

命令行调试：`python scripts/ehunt_etsy_store_query.py '<JSON>'`（需 `LINKFOXAGENT_API_KEY`）。详见 [references/api.md](references/api.md) 末尾。

## 参考

入参/出参表见 [references/api.md](references/api.md)。

<!-- LF_LARGE_RESPONSE_BLOCK -->
## Handling Large Responses

To avoid overflowing the agent context, persist the response to disk and extract only the fields you need:

```
python scripts/response_io.py run --script scripts/ehunt_etsy_store_query.py --out-dir <DIR> '<params>'
python scripts/response_io.py read <file> --fields "<paths>"   # or --path "<JMESPath>"
```

> Pick `--out-dir` outside any git working tree (e.g. `/tmp/...` on Unix, `%TEMP%/...` on Windows). Persisted responses may contain PII, pricing, or auth-sensitive data — do not commit them. Files are not auto-deleted; clean up when the task is done.

`run` writes the full response to a file and emits only a schema preview + file path. `read` projects specific fields, with `--limit/--offset` for slicing and `--format json|jsonl|csv|table` for output.

**When to prefer this pattern** — apply your judgment based on the response characteristics, e.g.:
- High field count per record, or fields you don't need
- Batch/paginated results (multiple items per call)
- Long-text fields (descriptions, reviews, HTML, time series)
- Output reused across later steps rather than consumed immediately

For small, single-use responses, calling the main script directly is fine.

⚠️ The preview is a truncated schema + sample, not the full data. Any field-level decision must read from the persisted file via `read`.
<!-- /LF_LARGE_RESPONSE_BLOCK -->
