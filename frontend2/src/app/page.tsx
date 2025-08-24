"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { WireframeCard, WireframeCardIcon, WireframeCardBody, WireframeNavigation } from "@/components/wireframe"
import { HomeBackground } from "@/components/ui/optimized-background"
import { ClipboardList, Clock, Star } from "lucide-react"
import { User } from "@/lib/types"

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const userData = localStorage.getItem('user')
    if (userData) {
      // User is logged in, redirect to dashboard
      window.location.href = '/dashboard'
      return
    }
    
    // No user found, show landing page
    setLoading(false)
  }, [])

  // Show loading while checking authentication
  if (loading) {
    return (
      <HomeBackground>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      </HomeBackground>
    )
  }
  return (
    <HomeBackground>
      {/* Navigation Header - Using reusable component */}
      <WireframeNavigation />

      {/* Main Content */}
      <main>
        {/* Hero Section */}
        <section className="text-center pt-24 pb-8 relative" role="banner" aria-label="Hero section">
          {/* Radial gradient background effect */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-radial from-wireframe-blue/10 to-transparent rounded-full -z-10" aria-hidden="true" />
          
          <div className="container max-w-[1400px] mx-auto px-6">
            <h1 className="text-clamp-hero font-extrabold text-wireframe-white mb-6 leading-tight bg-gradient-to-br from-white to-slate-300 bg-clip-text text-transparent">
              Find Your Perfect Career with AI
            </h1>
            
            <p className="text-xl text-wireframe-gray-light max-w-4xl mx-auto mb-12 leading-relaxed">
              Experience intelligent job matching powered by AI. Get personalized recommendations, auto-filled applications, and AI-powered interview preparation.
            </p>
            
            {/* Stats */}
            <div className="flex justify-center gap-12 mb-12 flex-wrap">
              <div className="bg-wireframe-glass-bg backdrop-blur-lg border border-wireframe-glass-border px-4 py-2 rounded-full text-wireframe-gray-medium text-sm transition-all duration-300 hover:bg-wireframe-glass-hover hover:-translate-y-0.5">
                <span className="text-wireframe-white font-bold">500+</span>
                <span className="ml-2">Open Positions</span>
              </div>
              <div className="bg-wireframe-glass-bg backdrop-blur-lg border border-wireframe-glass-border px-4 py-2 rounded-full text-wireframe-gray-medium text-sm transition-all duration-300 hover:bg-wireframe-glass-hover hover:-translate-y-0.5">
                <span className="text-wireframe-white font-bold">85%</span>
                <span className="ml-2">Faster Application Process</span>
              </div>
              <div className="bg-wireframe-glass-bg backdrop-blur-lg border border-wireframe-glass-border px-4 py-2 rounded-full text-wireframe-gray-medium text-sm transition-all duration-300 hover:bg-wireframe-glass-hover hover:-translate-y-0.5">
                <span className="text-wireframe-white font-bold">AI-Powered</span>
                <span className="ml-2">Matching & Screening</span>
              </div>
            </div>

            {/* Call to Action Buttons */}
            <div className="flex justify-center gap-6 flex-wrap mb-4" role="group" aria-label="Primary actions">
              <Link href="/jobs">
                <Button variant="primary" size="lg" aria-label="Browse all available job positions">
                  Browse Positions
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" size="lg" aria-label="Login to access personalized job matching">
                  Login to Get Matched
                </Button>
              </Link>
            </div>
            
            <p className="text-wireframe-gray-medium text-base">
              Join thousands of professionals finding their dream careers with AI
            </p>
          </div>
        </section>

        {/* Features Section */}
        <section className="container max-w-[1400px] mx-auto px-6 mb-16" id="features" aria-label="Platform features">
          <h2 className="sr-only">Key Features of Our AI-Powered Platform</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" role="list">
            <div role="listitem">
              <WireframeCard className="animate-fade-in">
                <WireframeCardBody>
                  <WireframeCardIcon color="blue">
                    <ClipboardList className="w-6 h-6" aria-hidden="true" />
                  </WireframeCardIcon>
                  <h3 className="text-xl font-bold text-wireframe-white mb-4">
                    AI-Powered Questions
                  </h3>
                  <p className="text-wireframe-gray-light leading-relaxed">
                    Dynamic question generation based on your resume and the role requirements. 
                    Each interview is personalized and challenging.
                  </p>
                </WireframeCardBody>
              </WireframeCard>
            </div>

            <div role="listitem">
              <WireframeCard className="animate-fade-in" style={{animationDelay: '0.2s'}}>
                <WireframeCardBody>
                  <WireframeCardIcon color="purple">
                    <Clock className="w-6 h-6" aria-hidden="true" />
                  </WireframeCardIcon>
                  <h3 className="text-xl font-bold text-wireframe-white mb-4">
                    Real-time Analysis
                  </h3>
                  <p className="text-wireframe-gray-light leading-relaxed">
                    Get instant feedback and follow-up questions based on your responses. 
                    The AI adapts to your expertise level.
                  </p>
                </WireframeCardBody>
              </WireframeCard>
            </div>

            <div role="listitem">
              <WireframeCard className="animate-fade-in" style={{animationDelay: '0.4s'}}>
                <WireframeCardBody>
                  <WireframeCardIcon color="green">
                    <Star className="w-6 h-6" aria-hidden="true" />
                  </WireframeCardIcon>
                  <h3 className="text-xl font-bold text-wireframe-white mb-4">
                    Comprehensive Feedback
                  </h3>
                  <p className="text-wireframe-gray-light leading-relaxed">
                    Detailed analysis of your performance with suggestions for improvement 
                    and strengths highlighted.
                  </p>
                </WireframeCardBody>
              </WireframeCard>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="container max-w-[1400px] mx-auto px-6" id="how-it-works">
          <h2 className="text-center text-4xl font-bold text-wireframe-white mb-12">
            How It Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { step: "1", title: "Upload Resume", description: "Share your resume for AI analysis and personalized matching" },
              { step: "2", title: "Find Matches", description: "Browse AI-recommended positions tailored to your profile" },
              { step: "3", title: "Apply Fast", description: "Complete applications in minutes with AI auto-fill" },
              { step: "4", title: "AI Interview", description: "Complete AI-powered interviews and get instant feedback" }
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-wireframe-blue to-wireframe-blue-dark text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto mb-4 shadow-wireframe-button">
                  {item.step}
                </div>
                <h3 className="text-lg font-bold text-wireframe-white mb-2">{item.title}</h3>
                <p className="text-wireframe-gray-light text-sm leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white/8 backdrop-blur-xl border-t border-white/15 text-wireframe-white py-6 mt-16">
        <div className="container max-w-[1400px] mx-auto px-6 text-center">
          <p className="text-wireframe-gray-medium">
            &copy; 2025 S Corp. Powered by MCP Mesh.
          </p>
        </div>
      </footer>
    </HomeBackground>
  )
}