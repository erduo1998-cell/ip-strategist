import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const COLORS = {
  ink: '#17211D',
  muted: '#69746F',
  paper: '#F7F3EA',
  panel: '#FFFDF8',
  line: '#DED8CB',
  green: '#286A51',
  greenSoft: '#E1EFE7',
  lime: '#BBD96B',
  coral: '#E26D4A',
  amber: '#F1B84B',
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const enter = (frame: number, at: number, duration = 16) =>
  interpolate(frame, [at, at + duration], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });

const stageOpacity = (frame: number, start: number, end: number) =>
  interpolate(frame, [start - 12, start, end, end + 12], [0, 1, 1, 0], clamp);

const DotGrid: React.FC = () => (
  <AbsoluteFill
    style={{
      opacity: 0.2,
      backgroundImage: 'radial-gradient(#69746F 1.2px, transparent 1.2px)',
      backgroundSize: '24px 24px',
      maskImage: 'linear-gradient(to bottom, black, transparent 78%)',
    }}
  />
);

const Wordmark: React.FC = () => (
  <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
    <div
      style={{
        width: 34,
        height: 34,
        borderRadius: 11,
        background: COLORS.green,
        color: COLORS.paper,
        display: 'grid',
        placeItems: 'center',
        fontWeight: 900,
        fontSize: 18,
      }}
    >
      ip
    </div>
    <div style={{fontWeight: 800, fontSize: 25, letterSpacing: -0.7}}>ip-strategist</div>
  </div>
);

const Badge: React.FC<{children: React.ReactNode; active?: boolean}> = ({children, active}) => (
  <div
    style={{
      border: `1px solid ${active ? COLORS.green : COLORS.line}`,
      background: active ? COLORS.greenSoft : COLORS.panel,
      color: active ? COLORS.green : COLORS.muted,
      borderRadius: 999,
      padding: '10px 16px',
      fontSize: 17,
      fontWeight: 700,
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </div>
);

const PromptStage: React.FC<{frame: number}> = ({frame}) => {
  const opacity = stageOpacity(frame, 0, 112);
  const card = enter(frame, 4, 18);
  const typed = Math.floor(interpolate(frame, [24, 86], [0, 24], clamp));
  const full = '播放 12 万，为什么只涨了 80 个粉？';
  return (
    <div style={{position: 'absolute', inset: 0, opacity}}>
      <div
        style={{
          position: 'absolute',
          left: 120,
          top: 198,
          width: 760,
          transform: `translateY(${(1 - card) * 24}px) scale(${0.98 + card * 0.02})`,
          opacity: card,
        }}
      >
        <div style={{fontSize: 18, color: COLORS.muted, fontWeight: 700, marginBottom: 16}}>
          直接说真实问题，不用先学方法
        </div>
        <div
          style={{
            background: COLORS.panel,
            border: `1px solid ${COLORS.line}`,
            borderRadius: 28,
            padding: '34px 38px',
            boxShadow: '0 22px 70px rgba(35, 54, 46, 0.10)',
            minHeight: 108,
            fontSize: 34,
            fontWeight: 750,
            letterSpacing: -1.1,
          }}
        >
          {full.slice(0, typed)}
          <span style={{color: COLORS.coral, opacity: frame % 18 < 10 ? 1 : 0}}>｜</span>
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          right: 122,
          top: 300,
          fontSize: 20,
          color: COLORS.green,
          fontWeight: 800,
          opacity: enter(frame, 82, 12),
          transform: `translateX(${(1 - enter(frame, 82, 12)) * 18}px)`,
        }}
      >
        一句话，开始工作 →
      </div>
    </div>
  );
};

const RouterStage: React.FC<{frame: number}> = ({frame}) => {
  const opacity = stageOpacity(frame, 112, 248);
  const labels = ['定位', '选题', '写稿', '增长', '复盘', '变现', '陪跑'];
  const chosen = enter(frame, 166, 20);
  const pulse = 1 + Math.sin((frame - 166) / 6) * 0.018 * chosen;
  return (
    <div style={{position: 'absolute', inset: 0, opacity}}>
      <div style={{position: 'absolute', top: 168, left: 0, right: 0, textAlign: 'center'}}>
        <div style={{fontSize: 20, color: COLORS.muted, fontWeight: 700}}>统一入口读懂当前任务</div>
        <div style={{fontSize: 46, fontWeight: 850, letterSpacing: -2, marginTop: 8}}>
          只点亮一个任务胶囊
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          top: 315,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          gap: 13,
        }}
      >
        {labels.map((label, index) => {
          const itemEnter = enter(frame, 130 + index * 5, 14);
          const active = label === '增长';
          return (
            <div
              key={label}
              style={{
                opacity: itemEnter * (active ? 1 : 1 - chosen * 0.58),
                transform: `translateY(${(1 - itemEnter) * 18}px) ${active ? `scale(${pulse})` : ''}`,
                filter: active ? 'none' : `grayscale(${chosen})`,
              }}
            >
              <Badge active={active && chosen > 0.5}>{label}</Badge>
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          top: 410,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          opacity: enter(frame, 184, 16),
        }}
      >
        <div style={{height: 1, width: 96, background: COLORS.line}} />
        <div style={{color: COLORS.green, fontSize: 19, fontWeight: 800}}>不默认通读整套方法论</div>
        <div style={{height: 1, width: 96, background: COLORS.line}} />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 494,
          left: '50%',
          width: 435,
          transform: `translateX(-50%) translateY(${(1 - enter(frame, 196, 18)) * 18}px)`,
          opacity: enter(frame, 196, 18),
          background: COLORS.ink,
          color: COLORS.paper,
          borderRadius: 22,
          padding: '20px 26px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 22px 56px rgba(23,33,29,.18)',
        }}
      >
        <span style={{fontWeight: 780, fontSize: 20}}>task-growth.md</span>
        <span style={{fontSize: 15, color: COLORS.lime, fontWeight: 800}}>唯一加载</span>
      </div>
    </div>
  );
};

const ResultStage: React.FC<{frame: number}> = ({frame}) => {
  const opacity = stageOpacity(frame, 248, 430);
  const card = spring({frame: frame - 256, fps: 30, config: {damping: 18, stiffness: 120}});
  const rate = interpolate(frame, [285, 330], [0, 0.067], clamp).toFixed(3);
  const action = enter(frame, 338, 18);
  return (
    <div style={{position: 'absolute', inset: 0, opacity}}>
      <div
        style={{
          position: 'absolute',
          left: 108,
          right: 108,
          top: 148,
          bottom: 105,
          display: 'grid',
          gridTemplateColumns: '0.86fr 1.14fr',
          gap: 22,
          transform: `translateY(${(1 - card) * 28}px) scale(${0.98 + card * 0.02})`,
          opacity: card,
        }}
      >
        <div
          style={{
            border: `1px solid ${COLORS.line}`,
            background: COLORS.panel,
            borderRadius: 28,
            padding: 32,
            boxShadow: '0 18px 55px rgba(35,54,46,.08)',
          }}
        >
          <div style={{fontSize: 16, color: COLORS.muted, fontWeight: 800}}>核心判断</div>
          <div style={{fontSize: 40, lineHeight: 1.16, fontWeight: 880, letterSpacing: -1.7, marginTop: 16}}>
            这是一条
            <br />
            <span style={{color: COLORS.coral}}>一次性赞藏型</span>
            <br />
            内容
          </div>
          <div style={{height: 1, background: COLORS.line, margin: '28px 0 22px'}} />
          <div style={{display: 'flex', alignItems: 'flex-end', gap: 11}}>
            <div style={{fontSize: 52, fontWeight: 900, color: COLORS.green, letterSpacing: -2}}>{rate}%</div>
            <div style={{fontSize: 16, color: COLORS.muted, fontWeight: 700, paddingBottom: 9}}>播放转粉率</div>
          </div>
          <div style={{color: COLORS.muted, fontSize: 17, lineHeight: 1.55, marginTop: 8}}>
            观众拿完工具名单，关系就结束了。
          </div>
        </div>
        <div
          style={{
            border: `1px solid ${COLORS.green}`,
            background: COLORS.green,
            color: COLORS.paper,
            borderRadius: 28,
            padding: 32,
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 20px 62px rgba(40,106,81,.22)',
          }}
        >
          <div
            style={{
              position: 'absolute',
              width: 320,
              height: 320,
              borderRadius: '50%',
              right: -120,
              top: -130,
              background: COLORS.lime,
              opacity: 0.18,
            }}
          />
          <div style={{fontSize: 16, color: COLORS.lime, fontWeight: 850}}>下一批，只改一个变量</div>
          <div style={{fontSize: 34, lineHeight: 1.2, fontWeight: 880, letterSpacing: -1.3, marginTop: 16}}>
            从“大合集”改成
            <br />
            “持续解一个场景”
          </div>
          <div style={{marginTop: 28, display: 'grid', gap: 12}}>
            {['固定一种目标人群', '每期跑通一个真实任务', '结尾预告下一期具体问题'].map((text, index) => {
              const item = enter(frame, 338 + index * 8, 16);
              return (
                <div
                  key={text}
                  style={{
                    display: 'flex',
                    gap: 13,
                    alignItems: 'center',
                    opacity: item * action,
                    transform: `translateX(${(1 - item) * 18}px)`,
                    fontSize: 19,
                    fontWeight: 720,
                  }}
                >
                  <span
                    style={{
                      width: 25,
                      height: 25,
                      borderRadius: 8,
                      background: COLORS.lime,
                      color: COLORS.ink,
                      display: 'grid',
                      placeItems: 'center',
                      fontWeight: 900,
                      fontSize: 15,
                    }}
                  >
                    {index + 1}
                  </span>
                  {text}
                </div>
              );
            })}
          </div>
          <div
            style={{
              position: 'absolute',
              left: 32,
              right: 32,
              bottom: 30,
              borderTop: '1px solid rgba(255,255,255,.22)',
              paddingTop: 18,
              color: '#DDE8E1',
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            交付判断、成品和下一步，不复述方法论
          </div>
        </div>
      </div>
    </div>
  );
};

export const IpStrategistDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const loopFade = interpolate(frame, [durationInFrames - 18, durationInFrames - 1], [1, 0], clamp);
  return (
    <AbsoluteFill
      style={{
        background: COLORS.paper,
        color: COLORS.ink,
        fontFamily: 'Inter, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif',
        overflow: 'hidden',
        opacity: loopFade,
      }}
    >
      <DotGrid />
      <div style={{position: 'absolute', top: 42, left: 54}}>
        <Wordmark />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 45,
          right: 54,
          fontSize: 16,
          color: COLORS.muted,
          fontWeight: 750,
        }}
      >
        虚构演示 · 一个入口 · 一个当前任务 · 一个可用结果
      </div>
      <PromptStage frame={frame} />
      <RouterStage frame={frame} />
      <ResultStage frame={frame} />
      <div
        style={{
          position: 'absolute',
          bottom: 26,
          left: 54,
          right: 54,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 14,
          color: COLORS.muted,
          fontWeight: 700,
        }}
      >
        <span>真实问题 → 唯一胶囊 → 直接交付</span>
        <span style={{color: COLORS.green}}>ip-strategist v2</span>
      </div>
    </AbsoluteFill>
  );
};
