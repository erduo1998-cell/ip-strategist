# 抖音评论本地数据源

只读拉取本人抖音创作者中心的一级评论正文和二级回复，再生成 IP 助手可读取的脱敏证据文件。Cookie 留在 Chrome；本工具不回复、不点赞、不删除，也不写 `ip-dossier.md`。

## 安装

需要 Node.js 20+、Chrome，以及 OpenCLI Browser Bridge 扩展。

```bash
npm install
npm run setup
```

按 OpenCLI 官方说明安装扩展后，建议在单独的 Chrome Profile 登录抖音创作者中心，并把该 Profile 命名为 `ip-douyin`：

```bash
./node_modules/.bin/opencli profile list
./node_modules/.bin/opencli profile rename <contextId> ip-douyin
```

## 同步

`--workdir` 指向实际存放 `ip-dossier.md` 的私人工作目录：

```bash
npm run sync -- \
  --workdir "/你的/IP工作目录" \
  --profile ip-douyin \
  --works 10
```

输出：

- `ip-evidence/douyin/comments-evidence.json`：脱敏、限量，供 IP 助手读取。
- `ip-evidence/douyin/raw/*.json`：本机原始采集结果，权限为仅当前用户可读写。

默认每个作品最多取 20 页一级评论、每条一级评论最多取 20 页回复。达到页数上限、接口返回不完整或回复展开失败时，证据会明确标为 `partial`，不会伪称全量。

## 真实限制

该能力使用抖音创作者中心内部接口，不是官方稳定 OpenAPI。登录过期、接口改版或平台风控都可能导致失败。工具不会绕过验证码或登录验证。
