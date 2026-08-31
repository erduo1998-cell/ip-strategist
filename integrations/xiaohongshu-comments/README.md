# 小红书本人账号评论接入（本地只读）

这是一条给 IP 助手使用的本地数据通道，只处理当前浏览器中本人账号发布的笔记：

- 从 `creator.xiaohongshu.com` 读取本人笔记列表和曝光、观看、点赞、收藏、评论、分享、涨粉等指标。
- 从 `www.xiaohongshu.com` 的本人主页解析这些笔记自己的 `xsec_token`，再读取评论正文与楼中楼回复。
- 不包含发布、回复、点赞、收藏、删除或全网搜索命令。
- 评论正文按“不可信外部数据”写入私有证据文件；作者昵称、主页链接和 `xsec_token` 不进入精简证据。

## 为什么需要两个登录态

小红书创作者中心负责“本人作品与数据指标”，普通网页版负责“带签名的笔记详情与评论”。二者的登录态可能独立，因此同一个 OpenCLI Profile 必须分别登录：

1. `https://creator.xiaohongshu.com/`
2. `https://www.xiaohongshu.com/explore`

采集器先取得创作者中心的本人笔记 ID，再只接受本人公开主页中出现的同一笔记 ID。若 ID 不属于当前登录账号，它会拒绝读取评论。因此即使传入其他公开笔记 ID，也不会变成全网采集器。

## 安装

```bash
cd integrations/xiaohongshu-comments
npm install
npm run setup
```

安装后确认命令存在：

```bash
opencli xiaohongshu ip-creator-comment-targets --help
opencli xiaohongshu ip-creator-comments --help
```

## 最小实测

先使用专用 Profile 登录上面两个站点，再运行：

```bash
opencli --profile <profile> xiaohongshu ip-creator-comment-targets \
  --limit 5 --profile_scrolls 12 -f json
```

选择一篇 `comment_count > 0` 且 `signed_url_available=true` 的本人笔记：

```bash
opencli --profile <profile> xiaohongshu ip-creator-comments <note_id> \
  --expected_comment_count <评论数> --limit 20 --pages 10 \
  --with_replies true --reply_pages 10 -f json
```

验证时不要把 JSON 发到聊天或提交到 Git。只需本地统计：一级评论数量、二级回复数量、正文非空数量，以及是否出现 `partial`。

## 同步到 IP 助手空间

工作目录必须已经有 `ip-dossier.md`：

```bash
npm run sync -- \
  --workdir /绝对路径/IP助手空间 \
  --profile <profile> \
  --works 10
```

也可以只同步约定作品；`--note` 可重复：

```bash
npm run sync -- \
  --workdir /绝对路径/IP助手空间 \
  --profile <profile> \
  --note 68aabbcc0000000011223344
```

输出：

- `ip-evidence/xiaohongshu/comments-evidence.json`：给 IP 助手读取的去身份化证据。
- `ip-evidence/xiaohongshu/raw/<时间>.json`：只保存在本机的原始采集结果。

两个文件均以 `0600` 权限写入。

## 完整性含义

- `complete`：页面已显示到采集终点或达到目标数量，并且可见楼中楼已展开完成，抓取数量与后台评论数相符。
- `partial`：页面懒加载、楼中楼按钮、风控或评论数口径使完整性不能确认。IP 助手仍可使用已有正文，但必须把它视为样本，不得声称是全量评论。

真实限制：小红书内部接口和 DOM 均不是稳定 OpenAPI。创作者中心签名由网页自身产生，采集器不内置或伪造签名；页面改版、登录失效、笔记非公开或触发风控时，需要重新登录或更新选择器。
