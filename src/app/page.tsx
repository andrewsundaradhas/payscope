"use client";

import { useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import ScrollAnimatedCard from "@/components/ScrollAnimatedCard";
import { FloatingCreditCard } from "@/components/FloatingCreditCard";

export default function Home() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"]
  });

  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95]);
  const heroY = useTransform(scrollYProgress, [0, 0.5], [0, -50]);

  const navItems = [
    { href: "/dashboard/insights", label: "insights" },
    { href: "/dashboard/reports", label: "reports" },
    { href: "/dashboard/chat", label: "chat" },
  ];

  return (
    <div className="min-h-[200vh] bg-[#FAFAFA] overflow-x-hidden">
      {/* Animated background blobs - lime green themed */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute -top-[40%] -left-[20%] w-[80%] h-[80%] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(190,242,100,0.2) 0%, transparent 70%)",
          }}
          animate={{
            x: [0, 50, 0],
            y: [0, 30, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute -bottom-[30%] -right-[20%] w-[70%] h-[70%] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(28,43,28,0.08) 0%, transparent 70%)",
          }}
          animate={{
            x: [0, -40, 0],
            y: [0, -20, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute top-[30%] right-[5%] w-[40%] h-[40%] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(190,242,100,0.15) 0%, transparent 60%)",
          }}
          animate={{
            x: [0, -30, 0],
            y: [0, 40, 0],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Navigation */}
      <motion.header 
        className="fixed top-0 left-0 right-0 z-50 px-6 py-5 bg-white/80 backdrop-blur-md border-b border-[#1C2B1C]/10"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <motion.div 
            className="flex items-center gap-2"
            whileHover={{ scale: 1.02 }}
          >
            <Link href="/" className="text-2xl font-black tracking-tight text-[#1C2B1C]">
              PayScope<span className="text-[#bef264]">.ai</span>
            </Link>
          </motion.div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#1C2B1C]/60">
            {navItems.map((item, i) => (
              <motion.div
                key={item.href}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
              >
                <Link
                  href={item.href}
                  className="hover:text-[#1C2B1C] transition-colors"
                >
                  <motion.span whileHover={{ y: -2 }} className="inline-block">
                    {item.label}
                  </motion.span>
                </Link>
              </motion.div>
            ))}
          </nav>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
          >
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1C2B1C] text-white text-sm font-semibold rounded-full hover:bg-[#2a3d2a] transition-all hover:shadow-lg hover:shadow-[#1C2B1C]/20"
            >
              join beta today
            </Link>
          </motion.div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <motion.section 
        ref={heroRef}
        className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-24"
        style={{ opacity: heroOpacity, scale: heroScale, y: heroY }}
      >
        {/* Floating Credit Cards - only in hero */}
        <FloatingCreditCard />
        
        <div className="relative z-10 max-w-5xl mx-auto text-center">
          {/* Main Headline */}
          <motion.h1 
            className="text-[clamp(3rem,10vw,8rem)] font-black leading-[0.9] tracking-tight text-[#1C2B1C]"
            initial={{ opacity: 0, y: 60 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.3 }}
          >
            <motion.span 
              className="block"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            >
              AI-powered
            </motion.span>
            <motion.span 
              className="block text-[#bef264]"
              style={{ textShadow: "2px 2px 0 #1C2B1C" }}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.7 }}
            >
              payment reporting.
            </motion.span>
          </motion.h1>

          {/* Subtext */}
          <motion.p 
            className="mt-8 text-lg md:text-xl text-[#1C2B1C]/60 max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.9 }}
          >
            Modernize Visa/Mastercard authorization, clearing, and settlement reports with GenAI:
            extract intelligence, chat in natural language, and ship dynamic dashboards instead of static files.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            className="mt-10"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 1.1 }}
          >
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#bef264] text-[#1C2B1C] text-base font-semibold rounded-full hover:bg-[#d4f794] transition-all hover:shadow-2xl hover:shadow-[#bef264]/40 hover:scale-105 border-2 border-[#1C2B1C]"
            >
              join beta today
              <motion.span
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                →
              </motion.span>
            </Link>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            className="mt-16 flex flex-col items-center gap-2 text-[#1C2B1C]/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
          >
            <span className="text-xs font-medium tracking-wider uppercase">scroll to explore</span>
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12l7 7 7-7" />
              </svg>
            </motion.div>
          </motion.div>
        </div>
      </motion.section>

      {/* Card Section */}
      <section className="relative py-20">
        <ScrollAnimatedCard />
      </section>

      {/* Cool Features Section */}
      <section className="relative py-24 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          {/* Section Header */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-8 mb-16">
            <motion.h2 
              className="text-5xl md:text-6xl font-black text-[#1C2B1C] leading-tight"
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              AI that<br /><span className="text-[#bef264]" style={{ textShadow: "1px 1px 0 #1C2B1C" }}>understands</span> reports.
            </motion.h2>
            <motion.p 
              className="text-[#1C2B1C]/60 max-w-sm leading-relaxed"
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Transform static Visa/Mastercard reports into interactive, insight-rich experiences:
              discovery, parsing, RAG-backed answers, and AI-generated visuals tailored to each institution.
            </motion.p>
          </div>

          {/* Feature Cards Grid */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Large Card - In-app Dashboard */}
            <motion.div
              className="md:row-span-2 rounded-3xl p-8 relative overflow-hidden border-2 border-[#1C2B1C]"
              style={{ backgroundColor: "#bef264" }}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              whileHover={{ scale: 1.02 }}
            >
              <h3 className="text-4xl md:text-5xl font-black text-[#1C2B1C] leading-tight mb-4">
                in-app<br />AI dashboards
              </h3>
              <Link 
                href="/dashboard/insights"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1C2B1C] text-white text-sm font-semibold rounded-full hover:bg-[#2a3d2a] transition-all"
              >
                Learn more
              </Link>
              
              {/* Chart visualization */}
              <div className="mt-8 bg-white/40 rounded-2xl p-4 border border-[#1C2B1C]/20">
                <div className="text-sm font-medium text-[#1C2B1C]/70 mb-2">Total visits ⓘ</div>
                <div className="relative h-32">
                  <svg viewBox="0 0 300 100" className="w-full h-full">
                    <path
                      d="M0 80 Q50 75 75 70 T150 50 T225 60 T300 30"
                      fill="none"
                      stroke="#1C2B1C"
                      strokeWidth="2"
                    />
                    <circle cx="225" cy="60" r="4" fill="#1C2B1C" />
                  </svg>
                  <div className="absolute top-0 right-0 bg-white rounded-lg px-3 py-1 shadow-lg text-sm font-bold text-[#1C2B1C]">
                    220,342,123
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Track Earnings Card */}
            <motion.div
              className="rounded-3xl p-8 relative overflow-hidden border border-[#E8E8E8]"
              style={{ backgroundColor: "#F5F5F5" }}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              whileHover={{ scale: 1.02 }}
            >
              <h3 className="text-3xl md:text-4xl font-black text-[#1C2B1C] leading-tight mb-4">
                RAG over<br />scheme reports
              </h3>
              <Link 
                href="/dashboard/reports"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#bef264] text-[#1C2B1C] text-sm font-semibold rounded-full hover:bg-[#d4f794] transition-all border border-[#1C2B1C]"
              >
                Learn more
              </Link>
              
              {/* Earnings list */}
              <div className="absolute right-6 top-6 text-right text-[#1C2B1C]/60 text-sm font-medium space-y-2">
                <div>Auth vs. settle <span className="text-xs text-[#bef264] bg-[#1C2B1C] px-1.5 py-0.5 rounded">drift</span></div>
                <div>Decline codes <span className="text-xs text-[#bef264] bg-[#1C2B1C] px-1.5 py-0.5 rounded">context</span></div>
                <div>Fee impacts <span className="text-xs text-[#bef264] bg-[#1C2B1C] px-1.5 py-0.5 rounded">per issuer</span></div>
                <div>Network splits <span className="text-xs text-[#bef264] bg-[#1C2B1C] px-1.5 py-0.5 rounded">live</span></div>
              </div>
            </motion.div>

            {/* Split Bills Card */}
            <motion.div
              className="rounded-3xl p-8 relative overflow-hidden border border-[#E8E8E8]"
              style={{ backgroundColor: "#E8E8E8" }}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              whileHover={{ scale: 1.02 }}
            >
              <h3 className="text-3xl md:text-4xl font-black text-[#1C2B1C] leading-tight mb-4">
                natural language<br />AI assistant
              </h3>
              <Link 
                href="/dashboard/chat"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1C2B1C] text-white text-sm font-semibold rounded-full hover:bg-[#2a3d2a] transition-all"
              >
                Learn more
              </Link>
              
              {/* Stacked bars visualization */}
              <div className="absolute right-6 top-6 flex gap-1">
                {[60, 80, 100, 70, 90].map((h, i) => (
                  <div 
                    key={i} 
                    className="w-6 rounded-t-lg"
                    style={{ 
                      height: `${h}px`, 
                      backgroundColor: `rgba(190, 242, 100, ${0.4 + i * 0.15})`,
                      border: "1px solid rgba(28,43,28,0.2)"
                    }}
                  />
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Different Levels Section */}
      <section className="relative py-24 px-6 bg-[#FAFAFA]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-8 mb-16">
            <motion.h2 
              className="text-5xl md:text-6xl font-black text-[#1C2B1C] leading-tight"
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              from static files<br />to <span className="text-[#bef264]" style={{ textShadow: "1px 1px 0 #1C2B1C" }}>live intelligence</span>.
            </motion.h2>
            <motion.div
              className="flex flex-col gap-4"
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <p className="text-[#1C2B1C]/60 max-w-sm leading-relaxed">
                Start with discovery and parsing of card scheme reports, add RAG for explainability,
                then layer in AI dashboards and forecasting. Built to adapt across clients and report types.
              </p>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1C2B1C] text-white text-sm font-semibold rounded-full hover:bg-[#2a3d2a] transition-all w-fit"
              >
                learn more
              </Link>
            </motion.div>
          </div>

          {/* Pricing/Level Cards */}
          <motion.div
            className="grid md:grid-cols-3 gap-6"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: 0.1 } }
            }}
          >
            {[
              { 
                name: "Discovery", 
                color: "#1C2B1C",
                borderColor: "#1C2B1C",
                textColor: "white",
                checkColor: "#bef264",
                features: ["Report cataloging", "Parsing pipelines", "Schema mapping"]
              },
              { 
                name: "Intelligence", 
                color: "#bef264",
                borderColor: "#1C2B1C",
                textColor: "#1C2B1C",
                checkColor: "#1C2B1C",
                features: ["RAG + LLM Q&A", "Anomaly surfacing", "Network/issuer splits", "Drift explanations"]
              },
              { 
                name: "Enterprise AI", 
                color: "#F5F5F5",
                borderColor: "#E8E8E8",
                textColor: "#1C2B1C",
                checkColor: "#bef264",
                features: ["Custom dashboards", "Forecasting & scenarios", "Multi-client theming", "Security & audit controls"]
              },
            ].map((tier, i) => (
              <motion.div
                key={i}
                className="rounded-3xl p-8 relative overflow-hidden border-2"
                style={{ 
                  backgroundColor: tier.color,
                  borderColor: tier.borderColor,
                }}
                variants={{
                  hidden: { opacity: 0, y: 40 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
                }}
                whileHover={{ y: -8 }}
              >
                <h3 className="text-2xl font-bold mb-6" style={{ color: tier.textColor }}>
                  {tier.name}
                </h3>
                <ul className="space-y-3" style={{ color: tier.textColor, opacity: 0.8 }}>
                  {tier.features.map((feature, j) => (
                    <li key={j} className="flex items-center gap-2">
                      <span style={{ color: tier.checkColor }}>✓</span> {feature}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative py-20 px-6 bg-[#1C2B1C]">
        <motion.div 
          className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.1 } }
          }}
        >
          {[
            { value: "92.1%", label: "Auth Success" },
            { value: "$1.9M", label: "Daily Volume" },
            { value: "142ms", label: "Avg Latency" },
            { value: "24/7", label: "Monitoring" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              className="text-center p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10"
              variants={{
                hidden: { opacity: 0, scale: 0.8 },
                visible: { opacity: 1, scale: 1, transition: { duration: 0.5 } }
              }}
              whileHover={{ scale: 1.05, borderColor: "rgba(190,242,100,0.5)" }}
            >
              <div className="text-3xl md:text-4xl font-black text-[#bef264]">{stat.value}</div>
              <div className="mt-2 text-sm text-white/60 font-medium">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Footer CTA */}
      <section className="relative py-32 px-6 bg-white">
        <motion.div 
          className="max-w-3xl mx-auto text-center"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="text-4xl md:text-5xl font-black text-[#1C2B1C] mb-6">
            Ready to simplify <span className="text-[#bef264]" style={{ textShadow: "1px 1px 0 #1C2B1C" }}>payments</span>?
          </h2>
          <p className="text-lg text-[#1C2B1C]/60 mb-10">
            Join thousands of payment teams who trust PayScope for their intelligence layer.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-10 py-5 bg-[#bef264] text-[#1C2B1C] text-lg font-semibold rounded-full hover:bg-[#d4f794] transition-all hover:shadow-2xl hover:shadow-[#bef264]/40 border-2 border-[#1C2B1C]"
          >
            Get started for free
          </Link>
        </motion.div>
      </section>
    </div>
  );
}
