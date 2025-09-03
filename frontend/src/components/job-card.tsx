"use client"

import { MapPin, Clock, Star, Bookmark, DollarSign } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { JobCardProps } from "@/lib/types"

export function JobCard({ 
  job, 
  variant = "detailed", 
  showMatchScore = false, 
  showBookmark = false,
  onApply,
  onBookmark,
  className,
  theme = "dark"
}: JobCardProps & { className?: string; theme?: "dark" | "light" }) {
  
  const handleApply = () => {
    onApply?.(job.id)
  }

  const handleBookmark = () => {
    onBookmark?.(job.id)
  }

  if (variant === "dashboard") {
    return (
      <div className={cn("bg-[#f8fafc] border border-[#e5e7eb] rounded-lg p-6", className)}>
        <div className="flex justify-between items-start mb-2">
          <a href={`/jobs/job/?id=${job.id}`} className="font-semibold text-red-600 hover:text-red-700 cursor-pointer underline">
            {job.title}
          </a>
          {showMatchScore && job.matchScore && (
            <div className={cn(
              "px-2 py-1 rounded text-xs font-semibold text-white",
              job.matchScore >= 95 ? "bg-[#10b981]" : "bg-[#3b82f6]"
            )}>
              {job.matchScore}% Match
            </div>
          )}
        </div>
        <p className="text-[#6b7280] text-sm mb-2 flex items-center gap-1">
          <MapPin className="w-3 h-3" /> {job.location} • <Clock className="w-3 h-3" /> {job.type} • <DollarSign className="w-3 h-3" /> {job.salaryRange ? `$${job.salaryRange.min}k-$${job.salaryRange.max}k` : 'Competitive'}
        </p>
        <p className="text-[#6b7280] text-sm">
          {job.description.slice(0, 80)}...
        </p>
      </div>
    )
  }

  if (variant === "compact") {
    return (
      <Card variant="flat" padding="sm" className={cn("border-b border-border rounded-none hover:bg-surface/50", className)}>
        <CardContent className="p-0">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <a href={`/jobs/job/?id=${job.id}`} className="font-semibold text-red-600 hover:text-red-700 cursor-pointer transition-colors truncate underline">
                {job.title}
              </a>
              <div className="flex items-center gap-4 text-sm text-text-secondary mt-1">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {job.type}
                </span>
              </div>
            </div>
            {showMatchScore && job.matchScore && (
              <div className="flex items-center gap-1 px-2 py-1 bg-success-500/10 text-success-500 rounded-full text-xs font-medium">
                <Star className="w-3 h-3 fill-current" />
                {job.matchScore}% match
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (variant === "featured") {
    return (
      <Card variant="glass" shimmer className={cn("border-primary-500/30 bg-primary-500/5", className)}>
        <CardContent>
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">{job.company[0]}</span>
                </div>
                <span className="text-sm font-medium text-text-secondary">{job.company}</span>
              </div>
              <a href={`/jobs/job/?id=${job.id}`} className="text-xl font-bold text-red-600 hover:text-red-700 cursor-pointer transition-colors mb-2 underline">{job.title}</a>
              <div className="flex items-center gap-4 text-sm text-text-secondary">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {job.type}
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {showMatchScore && job.matchScore && (
                <div className="flex items-center gap-1 px-3 py-1 bg-primary-500/20 text-primary-500 rounded-full text-sm font-semibold">
                  <Star className="w-4 h-4 fill-current" />
                  {job.matchScore}% match
                </div>
              )}
              {showBookmark && (
                <Button 
                  size="icon" 
                  variant="ghost"
                  onClick={handleBookmark}
                  className="text-text-secondary hover:text-primary-500"
                >
                  <Bookmark className={cn("w-5 h-5", job.isBookmarked && "fill-current text-primary-500")} />
                </Button>
              )}
            </div>
          </div>

          <p className="text-text-secondary text-sm leading-relaxed mb-6 line-clamp-2">
            {job.description}
          </p>

          <div className="flex items-center justify-between">
            <div className="flex flex-wrap gap-2">
              {job.requirements?.slice(0, 3).map((req, index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-surface/50 rounded-md text-xs text-text-secondary border border-border"
                >
                  {req}
                </span>
              ))}
            </div>
            <Button onClick={handleApply} size="sm">
              Apply Now
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Default detailed variant
  const cardVariant = theme === "light" ? "light" : "default"
  const textPrimary = theme === "light" ? "text-gray-900" : "text-foreground"
  const textSecondary = theme === "light" ? "text-gray-600" : "text-text-secondary"
  const textMuted = theme === "light" ? "text-gray-500" : "text-text-muted"
  const borderStyle = theme === "light" ? "border-gray-200" : "border-border"
  const bgSurface = theme === "light" ? "bg-gray-50" : "bg-surface"

  return (
    <Card variant={cardVariant} className={className}>
      <CardContent>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold">{job.company[0]}</span>
              </div>
              <div>
                <a href={`/jobs/job/?id=${job.id}`} className="text-lg font-bold text-red-600 hover:text-red-700 cursor-pointer transition-colors underline">
                  {job.title}
                </a>
                <span className={cn("text-sm font-medium", textSecondary)}>{job.company}</span>
              </div>
            </div>
            
            <div className={cn("flex items-center gap-4 text-sm mb-3", textSecondary)}>
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {job.location}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {job.type}
              </span>
              {job.salaryRange && (
                <span className={cn("px-2 py-1 rounded-md text-xs", bgSurface, borderStyle, "border")}>
                  ${job.salaryRange.min.toLocaleString()}-${job.salaryRange.max.toLocaleString()}
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {showMatchScore && job.matchScore && (
              <div className="flex items-center gap-1 px-3 py-1 bg-success-500/10 text-success-500 rounded-full text-sm font-semibold">
                <Star className="w-4 h-4 fill-current" />
                {job.matchScore}% match
              </div>
            )}
            {showBookmark && (
              <Button 
                size="icon" 
                variant="ghost"
                onClick={handleBookmark}
                className={cn("hover:text-primary-500", textSecondary)}
              >
                <Bookmark className={cn("w-5 h-5", job.isBookmarked && "fill-current text-primary-500")} />
              </Button>
            )}
          </div>
        </div>

        <p className={cn("text-sm leading-relaxed mb-4", textSecondary)}>
          {job.description}
        </p>

        {job.requirements && job.requirements.length > 0 && (
          <div className="mb-6">
            <h4 className={cn("text-sm font-semibold mb-2", textPrimary)}>Requirements:</h4>
            <div className="flex flex-wrap gap-2">
              {job.requirements.slice(0, 5).map((req, index) => (
                <span 
                  key={index}
                  className={cn("px-2 py-1 rounded-md text-xs border", bgSurface, textSecondary, borderStyle)}
                >
                  {req}
                </span>
              ))}
              {job.requirements.length > 5 && (
                <span className={cn("px-2 py-1 text-xs", textSecondary)}>
                  +{job.requirements.length - 5} more
                </span>
              )}
            </div>
          </div>
        )}

        <div className={cn("flex items-center justify-between pt-4 border-t", borderStyle)}>
          <div className={cn("text-xs", textMuted)}>
            Posted {new Date(job.postedAt).toLocaleDateString()}
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" size="sm">
              View Details
            </Button>
            <Button onClick={handleApply} size="sm">
              Apply Now
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}