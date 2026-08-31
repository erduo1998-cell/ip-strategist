import { cli, Strategy } from '@jackwener/opencli/registry';
import { fetchComments, fetchTargets } from './core.mjs';

cli({
  site: 'xiaohongshu',
  name: 'ip-creator-comment-targets',
  description: '只读列出本人小红书创作者中心笔记及基础指标',
  access: 'read',
  domain: 'creator.xiaohongshu.com',
  strategy: Strategy.COOKIE,
  navigateBefore: false,
  browser: true,
  defaultFormat: 'json',
  timeoutSeconds: 600,
  args: [
    { name: 'limit', type: 'int', default: 20 },
    { name: 'profile_scrolls', type: 'int', default: 12 },
    { name: 'include_signed_urls', type: 'bool', default: false },
  ],
  columns: [
    'data_source', 'rank', 'note_id', 'title', 'published_at', 'views',
    'impressions', 'likes', 'collects', 'comment_count', 'shares', 'rise_fans',
    'average_view_time', 'signed_url_available',
  ],
  func: fetchTargets,
});

cli({
  site: 'xiaohongshu',
  name: 'ip-creator-comments',
  description: '只读拉取本人小红书笔记评论正文与楼中楼回复',
  access: 'read',
  domain: 'www.xiaohongshu.com',
  strategy: Strategy.COOKIE,
  navigateBefore: false,
  browser: true,
  defaultFormat: 'json',
  timeoutSeconds: 900,
  args: [
    { name: 'note_id', type: 'string', required: true, positional: true },
    { name: 'expected_comment_count', type: 'int', default: 0 },
    { name: 'limit', type: 'int', default: 50 },
    { name: 'pages', type: 'int', default: 20 },
    { name: 'with_replies', type: 'bool', default: true },
    { name: 'reply_pages', type: 'int', default: 10 },
    { name: 'profile_scrolls', type: 'int', default: 12 },
  ],
  columns: [
    'data_source', 'rank', 'note_id', 'comment_id', 'comment_id_source',
    'parent_comment_id', 'root_comment_id', 'is_reply', 'reply_to', 'author',
    'text', 'likes', 'time', 'reply_count', 'fetched_reply_count',
    'reply_fetch_status', 'top_fetch_status', 'expected_comment_count',
    'source_url_path',
  ],
  func: fetchComments,
});
