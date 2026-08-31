# 视频号评论接入（本地只读）

此接入只读取当前浏览器中已登录的**本人视频号助手**：作品指标、一级评论正文与二级回复。它不读取私信/打招呼，不发送回复，不点赞、删除或修改任何平台数据。

## 安装

在这个目录运行：

```bash
npm install
npm run setup
```

然后在专用 Chrome Profile 中登录 `https://channels.weixin.qq.com` 的视频号助手，并确认 `opencli profile list` 显示该 Profile 已连接。

## 只读检查

```bash
node_modules/.bin/opencli --profile <profile> weixin-channels ip-creator-comment-targets --limit 5 -f json
node_modules/.bin/opencli --profile <profile> weixin-channels ip-creator-comments <object_id> --limit 20 --with_replies true -f json
```

## 写入本地 IP 证据

```bash
npm run sync -- --workdir <含 ip-dossier.md 的私人IP空间> --profile <profile>
```

只同步已签约的作品时，传 `--object-ids id1,id2`。原始数据与整理后的证据分别保存在 `ip-evidence/weixin-channels/raw/` 和 `ip-evidence/weixin-channels/comments-evidence.json`，文件权限为仅当前用户可读写。

视频号助手接口并非稳定公开 API；登录失效或后台改版时需重新验证适配器。
