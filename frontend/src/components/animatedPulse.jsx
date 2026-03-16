import { Warp } from '@paper-design/shaders-react';

export default function AnimatedPulse({ theme }) {
  return (
    <Warp
      colors={theme === 'dark' ? ["#16a34a", "#0a0a0a", "#0d0d0d"] : ["#7c3aed", "#f5f3ff", "#ede9fe"]}
      proportion={0.92}
      softness={0.9}
      distortion={0.5}
      swirl={0.75}
      swirlIterations={3}
      shape="checks"
      shapeScale={0.79}
      speed={1.5}
      scale={3}
      rotation={193}
      style={{ width: "100%", height: "100%" }}
    />
  )
}
