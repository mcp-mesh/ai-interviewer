import Image from 'next/image'
import { cn } from '@/lib/utils'

interface OptimizedBackgroundProps {
  src: string
  alt: string
  className?: string
  priority?: boolean
  quality?: number
  children?: React.ReactNode
}

export function OptimizedBackground({ 
  src, 
  alt, 
  className, 
  priority = false, 
  quality = 75,
  children 
}: OptimizedBackgroundProps) {
  return (
    <div className={cn("relative overflow-hidden", className)}>
      <Image
        src={src}
        alt={alt}
        fill
        priority={priority}
        quality={quality}
        className="object-cover object-center"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 100vw, 100vw"
        loading={priority ? "eager" : "lazy"}
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q=="
      />
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-black/50 to-black/70" />
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}

export function HomeBackground({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <OptimizedBackground
      src="/background.png"
      alt="AI Interviewer platform background"
      priority={true}
      quality={85}
      className={cn("min-h-screen", className)}
    >
      {children}
    </OptimizedBackground>
  )
}