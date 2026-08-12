import React from 'react';
import {Composition} from 'remotion';
import {IpStrategistDemo} from './IpStrategistDemo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="IpStrategistDemo"
      component={IpStrategistDemo}
      durationInFrames={450}
      fps={30}
      width={1400}
      height={788}
    />
  );
};
