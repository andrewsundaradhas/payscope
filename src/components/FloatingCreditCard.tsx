"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export function FloatingCreditCard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* Multiple floating cards at different positions - relative to hero section only */}
      {Array.from({ length: 6 }).map((_, i) => {
        const positions = [
          { left: "5%", top: "15%", scale: 0.8, mobile: true },
          { left: "80%", top: "25%", scale: 0.7, mobile: false },
          { left: "10%", top: "60%", scale: 0.9, mobile: true },
          { left: "85%", top: "65%", scale: 0.75, mobile: false },
          { left: "45%", top: "8%", scale: 0.65, mobile: false },
          { left: "55%", top: "75%", scale: 0.85, mobile: true },
        ];

        // Alternate between lime green and gray card styles
        const cardStyles = [
          { bg: "linear-gradient(135deg, #bef264 0%, #a3e635 50%, #84cc16 100%)", border: "#1C2B1C" },
          { bg: "linear-gradient(135deg, #F5F5F5 0%, #E8E8E8 50%, #D4D4D4 100%)", border: "#C4C4C4" },
          { bg: "linear-gradient(135deg, #1C2B1C 0%, #2a3d2a 50%, #3d503d 100%)", border: "#bef264" },
        ];

        const position = positions[i];
        const cardStyle = cardStyles[i % 3];
        const isDark = i % 3 === 2;
        
        return (
          <motion.div
            key={`card-${i}`}
            className={`absolute ${position.mobile ? 'hidden md:block' : ''}`}
            style={{
              left: position.left,
              top: position.top,
              transformStyle: "preserve-3d",
              perspective: "1000px",
              transform: `scale(${position.scale})`,
            }}
            animate={{
              rotateZ: [0, 360],
              y: [0, -30, 0],
              x: [0, Math.sin(i) * 20, 0],
              rotateY: [0, 15, -15, 0],
            }}
            transition={{
              duration: 18 + i * 4,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 1.5,
            }}
          >
            <div 
              className="relative w-64 h-40 rounded-2xl shadow-xl" 
              style={{ 
                perspective: "1000px",
                opacity: 0.5 + (i % 3) * 0.1,
              }}
            >
              {/* Card Front */}
              <motion.div
                className="absolute inset-0 rounded-2xl p-5 backdrop-blur-sm"
                style={{
                  transformStyle: "preserve-3d",
                  background: cardStyle.bg,
                  border: `2px solid ${cardStyle.border}`,
                  boxShadow: `0 8px 32px rgba(28, 43, 28, 0.15)`,
                }}
                animate={{
                  rotateY: [0, 360],
                  rotateX: [0, 8, -8, 0],
                  rotateZ: [0, 3, -3, 0],
                }}
                transition={{
                  duration: 25 + i * 6,
                  repeat: Infinity,
                  ease: "linear",
                  delay: i * 2,
                }}
              >
                {/* Holographic effect */}
                <div className="absolute inset-0 rounded-2xl overflow-hidden">
                  <div 
                    className="absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl"
                    style={{ background: isDark ? "rgba(190,242,100,0.15)" : "rgba(28,43,28,0.08)" }}
                  />
                  <div 
                    className="absolute bottom-0 left-0 w-24 h-24 rounded-full blur-xl"
                    style={{ background: isDark ? "rgba(190,242,100,0.1)" : "rgba(28,43,28,0.05)" }}
                  />
                </div>

                {/* Visa Logo - Top Right */}
                <div className="absolute top-5 right-5 z-10">
                  <svg viewBox="0 0 100 32" className="h-6 w-auto" fill={isDark ? "#bef264" : "#1C2B1C"}>
                    <path d="M40.4 1.2L26.3 30.8h-9.1L10.5 8.5c-.4-1.5-.7-2-1.9-2.6-1.9-1-5-1.9-7.7-2.5l.2-.9h14.6c1.9 0 3.5 1.2 4 3.3l3.6 19.1 8.9-22.5h9.2v.8zM72.6 21.3c0-7.9-10.9-8.3-10.8-11.8 0-1.1 1-2.2 3.3-2.5 1.1-.1 4.2-.3 7.7 1.3l1.4-6.4c-1.9-.7-4.3-1.3-7.4-1.3-7.8 0-13.3 4.1-13.4 10.1-.1 4.4 3.9 6.8 6.9 8.3 3.1 1.5 4.1 2.4 4.1 3.8 0 2-2.5 2.9-4.7 3-4 .1-6.3-1.1-8.1-1.9l-1.4 6.7c1.8.8 5.2 1.6 8.7 1.6 8.3 0 13.7-4.1 13.7-10.5v-.4zM93.5 30.8h8.1L94.3 1.2h-7.5c-1.7 0-3.1 1-3.7 2.5L70.8 30.8h9.2l1.8-5h11.2l1.1 5h-.6zm-9.8-11.9l4.6-12.7 2.6 12.7h-7.2zM48.5 1.2l-7.2 29.6h-8.8l7.2-29.6h8.8z" />
                  </svg>
                </div>

                {/* EMV Chip */}
                <div className="relative z-10 mb-3 mt-1">
                  <div 
                    className="w-10 h-7 rounded-md shadow-inner"
                    style={{ 
                      background: isDark ? "linear-gradient(135deg, #bef264, #84cc16)" : "linear-gradient(135deg, #1C2B1C, #2a3d2a)",
                      border: `1px solid ${isDark ? "#84cc16" : "#1C2B1C"}`
                    }}
                  >
                    <div className="w-full h-full grid grid-cols-3 gap-0.5 p-1">
                      {Array.from({ length: 6 }).map((_, idx) => (
                        <div 
                          key={idx} 
                          className="rounded-sm"
                          style={{ background: isDark ? "rgba(28,43,28,0.3)" : "rgba(190,242,100,0.3)" }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Card Number */}
                <div className="relative z-10 mb-4">
                  <p 
                    className="font-mono text-lg tracking-widest font-semibold"
                    style={{ color: isDark ? "#bef264" : "#1C2B1C" }}
                  >
                    4532 •••• •••• 8901
                  </p>
                </div>

                {/* Card Details Bottom */}
                <div className="relative z-10 flex justify-between items-end">
                  <div>
                    <p 
                      className="text-[10px] uppercase tracking-wider mb-0.5"
                      style={{ color: isDark ? "rgba(190,242,100,0.6)" : "rgba(28,43,28,0.6)" }}
                    >
                      Card Holder
                    </p>
                    <p 
                      className="text-xs font-semibold tracking-wide"
                      style={{ color: isDark ? "#bef264" : "#1C2B1C" }}
                    >
                      SARAH JOHNSON
                    </p>
                  </div>
                  <div className="text-right">
                    <p 
                      className="text-[10px] uppercase tracking-wider mb-0.5"
                      style={{ color: isDark ? "rgba(190,242,100,0.6)" : "rgba(28,43,28,0.6)" }}
                    >
                      Expires
                    </p>
                    <p 
                      className="text-xs font-semibold tracking-wide"
                      style={{ color: isDark ? "#bef264" : "#1C2B1C" }}
                    >
                      12/27
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Card Glow Effect */}
              <motion.div 
                className="absolute -inset-3 rounded-2xl blur-2xl"
                style={{ background: i % 3 === 0 ? "rgba(190,242,100,0.25)" : "rgba(28,43,28,0.15)" }}
                animate={{
                  opacity: [0.2, 0.4, 0.2],
                  scale: [1, 1.05, 1],
                }}
                transition={{
                  duration: 4 + i,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: i * 0.5,
                }}
              />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
