"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

export default function ScrollAnimatedCard() {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const rotateX = useTransform(scrollYProgress, [0, 0.5, 1], [25, 0, -15]);
  const rotateY = useTransform(scrollYProgress, [0, 0.5, 1], [-15, 0, 10]);
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.8, 1, 0.95]);
  const y = useTransform(scrollYProgress, [0, 0.5, 1], [100, 0, -50]);
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0, 1, 1, 0.8]);

  return (
    <div ref={containerRef} className="relative h-[500px] flex items-center justify-center perspective-[1500px]">
      <motion.div
        className="relative w-[340px] h-[220px] md:w-[420px] md:h-[260px] rounded-3xl overflow-hidden"
        style={{
          rotateX,
          rotateY,
          scale,
          y,
          opacity,
          transformStyle: "preserve-3d",
        }}
      >
        {/* Card face - lime green like the reference */}
        <div 
          className="absolute inset-0 rounded-3xl"
          style={{
            background: "linear-gradient(135deg, #d4fc79 0%, #96e6a1 50%, #84fab0 100%)",
            boxShadow: "0 25px 80px -12px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255,255,255,0.1) inset",
          }}
        />
        
        {/* Subtle noise texture */}
        <div 
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          }}
        />

        {/* Card content */}
        <div className="relative h-full flex items-center justify-between px-8 py-6">
          {/* Left vertical text */}
          <motion.div
            className="text-[#1a1a2e] font-black text-2xl md:text-3xl tracking-wide"
            style={{
              writingMode: "vertical-rl",
              textOrientation: "mixed",
              transform: "rotate(180deg)",
            }}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            PayScope
          </motion.div>

          {/* Center logo mark */}
          <motion.div 
            className="flex-1 flex items-center justify-center"
            initial={{ scale: 0, rotate: -180 }}
            whileInView={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.5, duration: 0.8, type: "spring" }}
          >
            <div className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-[#1a1a2e]/10 backdrop-blur-sm flex items-center justify-center">
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-[#1a1a2e]" />
            </div>
          </motion.div>

          {/* Right vertical text */}
          <motion.div
            className="text-[#1a1a2e] font-bold text-lg md:text-xl tracking-wide"
            style={{
              writingMode: "vertical-rl",
              textOrientation: "mixed",
              transform: "rotate(180deg)",
            }}
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            .ai
          </motion.div>
        </div>

        {/* Glossy reflection */}
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "linear-gradient(135deg, rgba(255,255,255,0.4) 0%, transparent 50%)",
          }}
        />
      </motion.div>
    </div>
  );
}
