"use client"

import { useRef, useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Camera, CameraOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// Dynamically import Webcam to avoid SSR issues
const Webcam = dynamic(() => import("react-webcam"), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-gray-800 animate-pulse" />
})

interface CameraPreviewProps {
  isEnabled?: boolean
  className?: string
}

export function CameraPreview({ isEnabled = true, className }: CameraPreviewProps) {
  const webcamRef = useRef<any>(null)
  const [hasError, setHasError] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const handleUserMedia = () => {
    setHasError(false)
  }

  const handleUserMediaError = () => {
    setHasError(true)
  }

  if (!isMounted) {
    return (
      <div className={cn("relative bg-gray-800 rounded-lg overflow-hidden animate-pulse", className)}>
        <div className="w-full h-full flex items-center justify-center">
          <Camera className="w-8 h-8 text-gray-400" />
        </div>
      </div>
    )
  }

  return (
    <div className={cn("relative bg-gray-900 rounded-lg overflow-hidden", className)}>
      {!hasError ? (
        <>
          <Webcam
            ref={webcamRef}
            audio={false}
            width="100%"
            height="100%"
            screenshotFormat="image/jpeg"
            videoConstraints={{
              width: 320,
              height: 240,
              facingMode: "user"
            }}
            onUserMedia={handleUserMedia}
            onUserMediaError={handleUserMediaError}
            className="w-full h-full object-cover"
          />
          
          {/* Recording indicator */}
          <div className="absolute top-2 left-2 flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-white text-xs font-medium bg-black/20 px-2 py-1 rounded">
              LIVE
            </span>
          </div>
        </>
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center text-white bg-gray-800">
          <div className="text-center">
            <CameraOff className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-gray-400">Camera not available</p>
          </div>
        </div>
      )}
    </div>
  )
}