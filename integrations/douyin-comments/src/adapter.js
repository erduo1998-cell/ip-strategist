import { cli, Strategy } from '@jackwener/opencli/registry';
import { CREATOR_COMMENT_URL, fetchComments, fetchTargets } from './core.mjs';

cli({
  site: 'douyin',
  name: 'ip-creator-comment-targets',
  description: '只读列出本人抖音创作者中心可采集评论的作品',
  access: 'read',
  domain: 'creator.douyin.com',
  strategy: Strategy.COOKIE,
  navigateBefore: CREATOR_COMMENT_URL,
  browser: true,
  defaultFormat: 'json',
  timeoutSeconds: 240,
  args: [
    { name: 'limit', type: 'int', default: 20 },
    { name: 'cursor', type: 'string', default: '0' },
    { name: 'pages', type: 'int', default: 1 },
    { name: 'wait_seconds', type: 'int', default: 2 },
  ],
  columns: [
    'data_source', 'rank', 'item_id', 'aweme_id', 'title', 'create_time',
    'publish_time', 'comment_count', 'has_more', 'next_cursor',
  ],
  func: fetchTargets,
});

cli({
  site: 'douyin',
  name: 'ip-creator-comments',
  description: '只读拉取本人抖音创作者中心评论正文与二级回复',
  access: 'read',
  domain: 'creator.douyin.com',
  strategy: Strategy.COOKIE,
  navigateBefore: CREATOR_COMMENT_URL,
  browser: true,
  defaultFormat: 'json',
  timeoutSeconds: 600,
  args: [
    { name: 'item_id', type: 'string', required: true, positional: true },
    { name: 'aweme_id', type: 'string', default: '' },
    { name: 'limit', type: 'int', default: 50 },
    { name: 'cursor', type: 'string', default: '0' },
    { name: 'pages', type: 'int', default: 20 },
    { name: 'sort', type: 'string', default: '' },
    { name: 'with_replies', type: 'bool', default: true },
    { name: 'reply_limit', type: 'int', default: 50 },
    { name: 'reply_pages', type: 'int', default: 20 },
    { name: 'wait_seconds', type: 'int', default: 2 },
  ],
  columns: [
    'data_source', 'rank', 'comment_id', 'item_id', 'author', 'author_uid',
    'author_sec_uid', 'avatar_url', 'text', 'time', 'create_time', 'ip_location',
    'digg_count', 'reply_count', 'reply_to', 'reply_to_comment_id',
    'parent_comment_id', 'root_comment_id', 'is_reply', 'fetched_reply_count',
    'reply_fetch_status', 'reply_fetch_error', 'has_more', 'next_cursor',
    'source_url_path',
  ],
  func: fetchComments,
});
