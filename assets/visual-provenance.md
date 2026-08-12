# Visual provenance

## `ip-strategist-hero.png` / `ip-strategist-hero.webp`

- 生成日期：2026-08-13
- 生成路径：Codex 内置 `imagegen` → GPT Image 2（无需 API key）
- 用例：`stylized-concept`，随后一次 `precise-object-edit`
- 输入来源：原创文字提示；未使用 `dbskill` 或其他第三方图片作为参考。最终编辑只使用本项目在同一轮生成的方向 B 作为编辑目标。
- 权利与限制：项目原创生成资产，按本仓库当前许可证发布；不包含已知第三方商标、平台 Logo、真实人物肖像、客户材料、数据截图或业绩数字。

### 方向选择

生成并实际查看了三个无字横版方向：A 为“编辑部桌面与光学教练”，B 为“纸艺档案馆收束为一张当前任务卡”，C 为“复杂信号经过棱镜成为成品”。选择 B，因为它最直接表达 v2 的核心产品结构：深层方法论被收纳在后台，用户眼前只有一个当前任务与一个可交付结果；缩小后仍能依靠“档案舱—单卡—创作者”的轮廓读懂。A 的室内摄影意味偏强，C 的艺术装置意味偏强。

### 选中方向提示词

```text
Use case: stylized-concept
Asset type: low-cost direction draft for a wide README hero image
Primary request: Create an original paper-sculpture visual metaphor for an AI IP coach that keeps a deep methodology organized but exposes only one current task and one useful next action to an independent creator.
Scene/backdrop: an abstract paper archive landscape on a clean deep-navy tabletop, wide horizontal frame.
Subject: dozens of layered blank paper folders, tabs, and branching sheets are neatly folded and compressed into one elegant translucent capsule-shaped viewing chamber at center; through the chamber, only one warm ivory blank card emerges toward a simple faceless wooden artist mannequin silhouette at the near edge, suggesting a creator without representing a real person.
Style/medium: premium handcrafted paper-cut editorial installation photographed as a real tabletop miniature; refined, original, tactile, intelligent.
Composition/framing: panoramic 16:9-feeling layout, layered depth from archive complexity in background to one clear card in foreground; all key forms inside central 65%, resilient to mobile center crop; calm negative space near corners.
Lighting/mood: soft museum-gallery lighting, one warm amber beam guiding the current card, quiet confidence and relief.
Color palette: ink navy, off-white paper, burnt orange accents, translucent smoky glass, small warm gold illumination; compatible with light and dark GitHub backgrounds.
Materials/textures: visible paper fibers, folded edges, matte wood, translucent resin, gentle shadows.
Constraints: absolutely no text, letters, numbers, glyphs, labels, charts, readable interface, logos, brands, watermarks, real faces, real people, data screenshots, or performance numbers; the mannequin must remain symbolic and faceless; no dbskill image reference or borrowed composition.
Avoid: book cover, literal software dashboard, generic robot, AI brain, circuit board, cyberpunk neon, random icons, clutter, illegible pseudo-writing.
```

### 最终单点迭代提示词

```text
Use case: precise-object-edit
Asset type: final wide README hero image
Primary request: Change only the foreground creator figure's scale and placement: make the same faceless wooden creator figure about 1.7 times larger and move it slightly forward and closer to the emerging blank card, so the relationship “creator receives one current task from the organized methodology archive” remains obvious at small README display size.
Input images: Image 1 is the edit target and selected direction.
Invariants: preserve the exact archival paper landscape, translucent capsule chamber, single emerging blank warm card, viewing angle, horizontal composition, lighting, palette, materials, depth, camera, and all other objects unchanged. Keep the central archive as the dominant object. Keep the creator clearly symbolic, wooden, fictional, and faceless. Keep all important forms resilient to a center mobile crop.
Constraints: absolutely no text, letters, numbers, glyphs, labels, charts, readable interface, logos, brands, watermarks, real faces, real people, data screenshots, or numerical performance claims. No new objects.
Avoid: changing the archive, adding a face, enlarging the creator so much it competes with the archive, pseudo-writing, UI, robot styling.
```

### 交付处理

- PNG：1360 × 765，RGB，无透明通道，保留为高质量发布素材。
- WebP：1360 × 765，质量 82，用于 README。
- 只保留最终选中方向；三张方向稿和编辑过程图不进入仓库。

## Remotion 产品演示

- 资产：`ip-strategist-demo.gif`、`ip-strategist-demo.mp4`、`ip-strategist-demo-poster.png`
- 可复现源码：`demo/remotion/`
- 渲染引擎：Remotion 4.0.508
- 生成日期：2026-08-13
- 内容边界：演示中的“12 万播放、80 个涨粉”是用于说明增长诊断流程的虚构数据，不对应真实客户、账号或业绩。
- 原创说明：信息架构、视觉系统、动效、文案和代码均为本项目独立制作；没有复制参考项目的动画、终端录屏、配色或布局。

## 作者联系二维码

- 资产：`wechat-qrcode.jpg`
- 来源：作者本人长期公开使用的个人微信二维码，与 `erduo-broll-loop-engineering/docs/images/wechat-contact.jpg` 和 ReachSurge 公开联系资产一致。
- 使用边界：仅用于作者联系、1v1 IP 咨询与商业授权入口；咨询服务与商业使用许可彼此独立。
- 处理说明：复用既有公开资产，未重新生成、未解码、未修改二维码内容。
