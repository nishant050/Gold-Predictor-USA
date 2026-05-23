'use client';

import { useEffect, useState } from 'react';

export default function AnimatedNumber({ value, prefix = '', suffix = '', duration = 800 }) {
  const [display, setDisplay] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const end = Number(value) || 0;
    if (end === 0) {
      setDisplay(0);
      return;
    }
    const startTime = performance.now();
    
    let animationFrameId;
    
    function animate(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplay(start + (end - start) * eased);
      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    }
    
    animationFrameId = requestAnimationFrame(animate);
    
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [value, duration]);
  
  return (
    <>
      {prefix}
      {display.toLocaleString(undefined, { 
        minimumFractionDigits: 2,
        maximumFractionDigits: 2 
      })}
      {suffix}
    </>
  );
}
