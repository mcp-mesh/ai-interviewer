"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Navigation } from "@/components/navigation"
import { WireframeButton } from "@/components/wireframe/WireframeButton"
import { ToastContainer, useToast } from "@/components/wireframe"
import { UserState, User } from "@/lib/types"

interface PreparePageProps {
  params: Promise<{ jobId: string }>
}

export default function InterviewPreparePage({ params }: PreparePageProps) {
  const [jobId, setJobId] = useState<string>("")
  const [user] = useState<User | null>({
    id: "1",
    name: "Dhyan Raj",
    email: "dhyan.raj@gmail.com"
  })
  const userState: UserState = "logged-in"
  const { toasts, showToast, removeToast } = useToast()

  useEffect(() => {
    const resolveParams = async () => {
      const resolvedParams = await params
      setJobId(resolvedParams.jobId)
    }
    resolveParams()
  }, [params])

  const handleStartInterview = () => {
    showToast.info('Starting your interview...')
    // In a real implementation, this would redirect to the actual interview interface
    setTimeout(() => {
      showToast.info('Interview session would start here. This would redirect to the actual AI interview interface.')
    }, 1500)
  }

  const handleGoBack = () => {
    window.location.href = '/dashboard'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container mx-auto px-6 py-8">
        {/* Two-column layout */}
        <div className="flex gap-8">
          {/* Main Content */}
          <div className="flex-1">
            {/* Job Header */}
            <div className="mb-8">
              <h1 className="text-red-600 text-4xl font-bold mb-4 leading-tight">Senior Software Engineer</h1>
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-6 text-gray-500 text-sm">
                  <div className="flex items-center gap-1">
                    📅 Interview Duration: 30 minutes
                  </div>
                  <div className="flex items-center gap-1">
                    📍 San Francisco, CA
                  </div>
                  <div className="flex items-center gap-1">
                    🕐 Full Time
                  </div>
                </div>
                <div className="flex gap-4">
                  <WireframeButton 
                    variant="secondary" 
                    size="md" 
                    onClick={handleGoBack}
                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    I Need More Time
                  </WireframeButton>
                  <WireframeButton 
                    variant="primary" 
                    size="md" 
                    onClick={handleStartInterview}
                    className="px-6 py-3"
                  >
                    I'm Ready - Start Interview
                  </WireframeButton>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mb-8 text-red-600 text-sm">
              <Link href="/dashboard" className="text-red-600 no-underline flex items-center gap-2 hover:text-red-700">
                ← Back to Dashboard
              </Link>
            </div>

            {/* Interview Rules Section */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-8 mb-12">
              <h2 className="text-xl font-semibold text-red-600 mb-6 flex items-center gap-2">
                ⚠️ Interview Guidelines & Rules
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-red-800 mb-3">🚫 Prohibited Activities</h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>Copy & Paste:</strong> Copying and pasting text is disabled during the interview</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>Tab Switching:</strong> Switching to other browser tabs or applications is not allowed</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>JavaScript Modification:</strong> Attempting to modify browser developer tools or JavaScript is prohibited</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>External Assistance:</strong> Using external resources, tools, or getting help from others during the interview</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3">⚖️ Violation Policy</h4>
                  <p className="text-red-900 mb-4">Our AI monitoring system will detect violations and respond as follows:</p>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-amber-500 font-bold">1st & 2nd Violation:</span>
                      <span>You will receive a warning and the interview will continue</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-600 font-bold">3rd Violation:</span>
                      <span>The interview will be automatically terminated and marked as incomplete</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3">⏰ Time Management</h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Duration:</strong> This interview is scheduled for 30 minutes</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Auto-End:</strong> The interview will automatically end when time expires</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Manual Exit:</strong> You can end the interview early at any time using the "End Interview" button</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3">🔧 Technical Issues & Recovery</h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Reconnection Window:</strong> If technical issues occur, you can reconnect and resume your interview as long as the total scheduled time hasn't elapsed</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Example:</strong> If your interview starts at 2:00 PM for 30 minutes, you can reconnect until 2:30 PM, even if you were disconnected</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Progress Saved:</strong> Your answers and progress will be automatically saved and restored upon reconnection</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Role Description */}
            <div className="bg-white border border-gray-200 rounded-xl p-8">
              <h2 className="text-xl font-semibold text-gray-800 mb-6">About This Role</h2>
              
              <p className="leading-relaxed mb-6 text-gray-600">
                The Software Engineering team at S Corp. is growing rapidly and is seeking new members for our platform development team. The platform team is responsible for building scalable web applications that serve millions of users worldwide. As a Senior Software Engineer, you will be responsible for designing and implementing robust, scalable solutions using modern web technologies.
              </p>

              <h3 className="text-lg font-semibold mt-8 mb-4 text-gray-800">What you will do:</h3>
              <ul className="list-disc pl-6 text-gray-600 leading-relaxed">
                <li className="mb-2">Design and develop high-quality, scalable web applications using React, Node.js, and cloud technologies</li>
                <li className="mb-2">Collaborate with cross-functional teams including product managers, designers, and other engineers</li>
                <li className="mb-2">Participate in code reviews and maintain high coding standards across the team</li>
                <li className="mb-2">Architect and implement APIs and microservices for our platform infrastructure</li>
                <li className="mb-2">Mentor junior developers and contribute to team knowledge sharing</li>
                <li className="mb-2">Optimize application performance and ensure reliability at scale</li>
              </ul>

              <h3 className="text-lg font-semibold mt-8 mb-4 text-gray-800">What we need from you:</h3>
              <ul className="list-disc pl-6 text-gray-600 leading-relaxed">
                <li className="mb-2">BS/MS degree in Computer Science, Engineering, or related field, or equivalent experience</li>
                <li className="mb-2">5+ years of professional software development experience</li>
                <li className="mb-2">Strong proficiency in JavaScript, React, and Node.js</li>
                <li className="mb-2">Experience with cloud platforms (AWS, GCP, or Azure)</li>
                <li className="mb-2">Solid understanding of database design and SQL</li>
                <li className="mb-2">Experience with RESTful APIs and microservices architecture</li>
                <li className="mb-2">Strong problem-solving skills and attention to detail</li>
                <li className="mb-2">Excellent communication skills and ability to work in a collaborative environment</li>
              </ul>

              <h3 className="text-lg font-semibold mt-8 mb-4 text-gray-800">What we would like from you:</h3>
              <ul className="list-disc pl-6 text-gray-600 leading-relaxed">
                <li className="mb-2">Experience with TypeScript and modern frontend build tools</li>
                <li className="mb-2">Knowledge of containerization technologies (Docker, Kubernetes)</li>
                <li className="mb-2">Experience with testing frameworks and CI/CD pipelines</li>
                <li className="mb-2">Contributions to open-source projects</li>
                <li className="mb-2">Experience with agile development methodologies</li>
              </ul>

              <h3 className="text-lg font-semibold mt-8 mb-4 text-gray-800">Benefits and Perks:</h3>
              <p className="leading-relaxed text-gray-600">
                We offer competitive compensation including base salary, equity, and comprehensive benefits. Our benefits package includes healthcare (medical, dental, vision), 401(k) match, unlimited PTO, flexible working arrangements, professional development stipend, and access to cutting-edge technology. We also provide catered meals, gym membership, and a collaborative work environment in our modern office space.
              </p>
            </div>
          </div>

          {/* Sidebar */}
          <aside className="w-80 space-y-8">
            {/* Interview Info */}
            <div className="border border-gray-200 rounded-lg p-6 bg-blue-50">
              <h4 className="font-semibold mb-4 text-blue-900">Interview Information</h4>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Position:</span>
                  <span className="text-blue-900 font-medium">Senior Software Engineer</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Duration:</span>
                  <span className="text-blue-900 font-medium">30 minutes</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Type:</span>
                  <span className="text-blue-900 font-medium">AI-Powered Technical</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Questions:</span>
                  <span className="text-blue-900 font-medium">8-12 questions</span>
                </div>
              </div>
            </div>

            {/* Preparation Tips */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold mb-4 text-gray-800">💡 Preparation Tips</h4>
              <ul className="list-none p-0 text-sm text-gray-600">
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-emerald-500">✓</span>
                  <span>Ensure stable internet connection</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-emerald-500">✓</span>
                  <span>Use a quiet environment</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-emerald-500">✓</span>
                  <span>Close unnecessary applications</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-emerald-500">✓</span>
                  <span>Have your resume nearby for reference</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-500">✓</span>
                  <span>Test your microphone and camera</span>
                </li>
              </ul>
            </div>

            {/* Technical Requirements */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold mb-4 text-gray-800">🔧 Technical Requirements</h4>
              <ul className="list-none p-0 text-sm text-gray-600">
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Chrome, Firefox, Safari, or Edge browser</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Microphone access for voice responses</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Camera access for verification</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Minimum 5 Mbps internet speed</span>
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </main>
      
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}