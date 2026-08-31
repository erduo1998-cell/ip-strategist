import { cli, Strategy } from '@jackwener/opencli/registry';
import { CREATOR_COMMENT_URL, CREATOR_POST_URL, fetchComments, fetchTargets } from './core.mjs';

cli({
  site: 'weixin-channels', name: 'ip-creator-comment-targets',
  description: '只读列出本人视频号助手可复盘的作品与指标', access: 'read',
  domain: 'channels.weixin.qq.com', strategy: Strategy.COOKIE, navigateBefore: CREATOR_POST_URL,
  browser: true, defaultFormat: 'json', timeoutSeconds: 240,
  args: [
    { name: 'limit', type: 'int', default: 20 }, { name: 'page', type: 'int', default: 1 },
    { name: 'pages', type: 'int', default: 1 },
  ],
  columns: ['data_source', 'rank', 'object_id', 'title', 'media_type', 'publish_time', 'view_count', 'like_count', 'fav_count', 'share_count', 'comment_count', 'unread_comment_count'],
  func: fetchTargets,
});

cli({
  site: 'weixin-channels', name: 'ip-creator-comments',
  description: '只读拉取本人视频号助手作品的评论正文与二级回复', access: 'read',
  domain: 'channels.weixin.qq.com', strategy: Strategy.COOKIE, navigateBefore: CREATOR_COMMENT_URL,
  browser: true, defaultFormat: 'json', timeoutSeconds: 600,
  args: [
    { name: 'object_id', type: 'string', required: true, positional: true },
    { name: 'limit', type: 'int', default: 50 }, { name: 'cursor', type: 'string', default: '' },
    { name: 'pages', type: 'int', default: 20 }, { name: 'with_replies', type: 'bool', default: true },
    { name: 'reply_limit', type: 'int', default: 50 }, { name: 'reply_pages', type: 'int', default: 20 },
  ],
  columns: ['data_source', 'rank', 'comment_id', 'object_id', 'parent_comment_id', 'root_comment_id', 'is_reply', 'text', 'time', 'like_count', 'reply_count', 'fetched_reply_count', 'reply_fetch_status', 'reply_fetch_error', 'has_more', 'next_cursor', 'traversal_complete'],
  func: fetchComments,
});
