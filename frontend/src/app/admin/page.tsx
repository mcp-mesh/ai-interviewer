'use client'

import { useState, useEffect } from 'react'
import { 
  Users,
  Briefcase,
  Search,
  Plus,
  Edit,
  Trash2,
  Eye,
  User as UserIcon,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { User } from '@/lib/types'

interface Job {
  job_id: string
  title: string
  description: string
  status: string
  duration: number
  created_at: string
  created_by: string
  updated_at?: string
  updated_by?: string
  interview_count?: number
}

interface AdminUser {
  email: string
  name: string
  admin: boolean
  blocked?: boolean
  created_at: string
  last_login: string
  provider: string
  notes?: string
}

export default function AdminPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'jobs' | 'users'>('jobs')
  const [jobs, setJobs] = useState<Job[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [jobSearchTerm, setJobSearchTerm] = useState('')
  const [userSearchTerm, setUserSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null)
  const [showUserModal, setShowUserModal] = useState(false)

  const [userFormData, setUserFormData] = useState({
    admin: false,
    blocked: false,
    notes: ''
  })

  useEffect(() => {
    loadCurrentUser()
    loadJobs()
    loadUsers()
  }, [])

  const loadCurrentUser = async () => {
    try {
      const { userApi } = await import('@/lib/api')
      const result = await userApi.getProfile()
      
      if (result.data) {
        setCurrentUser(result.data)
        // Store real user data in localStorage for consistency
        localStorage.setItem('user', JSON.stringify(result.data))
      } else {
        // No user data found, redirect to login
        window.location.href = '/login?redirect=/admin'
      }
    } catch (error) {
      console.error('Failed to load current user:', error)
      // API call failed (likely not authenticated), redirect to login
      window.location.href = '/login?redirect=/admin'
    }
  }

  const handleLogout = async () => {
    try {
      await fetch('/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
    window.location.href = '/'
  }

  const loadJobs = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/admin/jobs', {
        credentials: 'include'
      })
      if (response.ok) {
        const result = await response.json()
        // API returns jobs in the data field, map to expected format
        const jobsData = result.data?.map((job: any) => ({
          job_id: job.id,
          title: job.title,
          description: job.description || '',
          status: job.status,
          duration: job.interview_duration_minutes,
          created_at: job.created_at,
          created_by: job.created_by,
          updated_at: job.updated_at,
          updated_by: job.updated_by,
          interview_count: job.interview_count || 0
        })) || []
        setJobs(jobsData)
      } else {
        setError('Failed to load jobs')
      }
    } catch (error) {
      console.error('Load jobs error:', error)
      setError('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/admin/users', {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setUsers(data.data || [])
      } else {
        setError('Failed to load users')
      }
    } catch (error) {
      console.error('Load users error:', error)
      setError('Failed to load users')
    } finally {
      setLoading(false)
    }
  }


  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return
    
    try {
      const response = await fetch(`/api/admin/jobs/${jobId}`, {
        method: 'DELETE',
        credentials: 'include'
      })
      
      if (response.ok) {
        loadJobs()
      } else {
        setError('Failed to delete job')
      }
    } catch (error) {
      console.error('Delete job error:', error)
      setError('Failed to delete job')
    }
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return
    
    try {
      const response = await fetch(`/api/admin/users/${encodeURIComponent(selectedUser.email)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(userFormData)
      })
      
      if (response.ok) {
        setShowUserModal(false)
        setSelectedUser(null)
        setUserFormData({ admin: false, blocked: false, notes: '' })
        loadUsers()
      } else {
        setError('Failed to update user')
      }
    } catch (error) {
      console.error('Update user error:', error)
      setError('Failed to update user')
    }
  }


  const openUserModal = (user: AdminUser) => {
    setSelectedUser(user)
    setUserFormData({
      admin: user.admin,
      blocked: user.blocked || false,
      notes: user.notes || ''
    })
    setShowUserModal(true)
  }

  const filteredJobs = jobs.filter(job =>
    job.title.toLowerCase().includes(jobSearchTerm.toLowerCase()) ||
    job.description.toLowerCase().includes(jobSearchTerm.toLowerCase())
  )

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
  )

  // Don't render if not admin
  if (currentUser && !currentUser.isAdmin && !currentUser.is_admin) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation 
          userState="has-resume" 
          user={currentUser} 
          theme="light"
          currentPage="admin"
        />
        <div className="container mx-auto px-4 py-8">
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center shadow-sm">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-500" />
            <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
            <p className="text-gray-600">You don't have permission to access this page.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation 
        userState="has-resume" 
        user={currentUser} 
        theme="light"
        currentPage="admin"
      />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
            <p className="text-gray-600 text-lg">Manage jobs and users</p>
          </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 shadow-sm">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className="text-red-700">{error}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setError('')}
                    className="ml-auto text-red-500 hover:bg-red-100"
                  >
                    ×
                  </Button>
                </div>
              </div>
            )}

            {/* Tabs */}
            <div className="flex border-b border-gray-200 mb-6">
              <button
                onClick={() => setActiveTab('jobs')}
                className={cn(
                  "flex items-center gap-2 px-6 py-3 font-medium border-b-2 transition-colors",
                  activeTab === 'jobs'
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                <Briefcase className="w-5 h-5" />
                Jobs ({jobs.length})
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={cn(
                  "flex items-center gap-2 px-6 py-3 font-medium border-b-2 transition-colors",
                  activeTab === 'users'
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                <Users className="w-5 h-5" />
                Users ({users.length})
              </button>
            </div>

            {/* Jobs Tab */}
            {activeTab === 'jobs' && (
              <div>
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                  <div className="relative flex-1">
                    <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search jobs..."
                      value={jobSearchTerm}
                      onChange={(e) => setJobSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <Link href="/admin/jobs/create">
                    <Button className="flex items-center gap-2">
                      <Plus className="w-4 h-4" />
                      Add Job
                    </Button>
                  </Link>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition-all duration-200">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Title</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Status</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Duration</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Created</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Interviews</th>
                          <th className="text-right py-4 px-6 font-medium text-gray-900">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {loading ? (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-gray-500">
                              Loading...
                            </td>
                          </tr>
                        ) : filteredJobs.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-gray-500">
                              No jobs found
                            </td>
                          </tr>
                        ) : (
                          filteredJobs.map((job) => (
                            <tr key={job.job_id} className="border-b border-gray-100 hover:bg-gray-50">
                              <td className="py-4 px-6">
                                <div>
                                  <div className="font-medium text-gray-900">{job.title}</div>
                                  <div className="text-sm text-gray-500 truncate max-w-xs">
                                    {job.description}
                                  </div>
                                </div>
                              </td>
                              <td className="py-4 px-6">
                                <span className={cn(
                                  "inline-flex px-2 py-1 text-xs font-medium rounded-full",
                                  job.status === 'open' && "bg-green-100 text-green-800",
                                  job.status === 'closed' && "bg-red-100 text-red-800",
                                  job.status === 'on_hold' && "bg-yellow-100 text-yellow-800"
                                )}>
                                  {job.status}
                                </span>
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {job.duration} min
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {new Date(job.created_at).toLocaleDateString()}
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {job.interview_count || 0}
                              </td>
                              <td className="py-4 px-6">
                                <div className="flex items-center gap-2 justify-end">
                                  <Link href={`/admin/job-details?id=${job.job_id}`}>
                                    <Button size="sm" variant="ghost">
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                  </Link>
                                  <Link href={`/admin/jobs/edit/${job.job_id}`}>
                                    <Button size="sm" variant="ghost">
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                  </Link>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleDeleteJob(job.job_id)}
                                    className="text-red-600 hover:bg-red-50"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div>
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                  <div className="relative flex-1">
                    <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={userSearchTerm}
                      onChange={(e) => setUserSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition-all duration-200">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-4 px-6 font-medium text-gray-900">User</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Status</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Provider</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Created</th>
                          <th className="text-left py-4 px-6 font-medium text-gray-900">Last Login</th>
                          <th className="text-right py-4 px-6 font-medium text-gray-900">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {loading ? (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-gray-500">
                              Loading...
                            </td>
                          </tr>
                        ) : filteredUsers.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-gray-500">
                              No users found
                            </td>
                          </tr>
                        ) : (
                          filteredUsers.map((user) => (
                            <tr key={user.email} className="border-b border-gray-100 hover:bg-gray-50">
                              <td className="py-4 px-6">
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <UserIcon className="w-4 h-4 text-blue-600" />
                                  </div>
                                  <div>
                                    <div className="font-medium text-gray-900">{user.name}</div>
                                    <div className="text-sm text-gray-500">{user.email}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="py-4 px-6">
                                <div className="flex items-center gap-2">
                                  {user.admin && (
                                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                                      Admin
                                    </span>
                                  )}
                                  {user.blocked && (
                                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                                      Blocked
                                    </span>
                                  )}
                                  {!user.admin && !user.blocked && (
                                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                      Active
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {user.provider}
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {new Date(user.created_at).toLocaleDateString()}
                              </td>
                              <td className="py-4 px-6 text-gray-900">
                                {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                              </td>
                              <td className="py-4 px-6">
                                <div className="flex items-center gap-2 justify-end">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openUserModal(user)}
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

        {/* User Modal */}
        {showUserModal && selectedUser && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white border border-gray-200 rounded-xl shadow-lg w-full max-w-lg">
              <div className="p-6">
                <h2 className="text-xl font-bold mb-4">
                  Edit User: {selectedUser.name}
                </h2>
                
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="admin"
                      checked={userFormData.admin}
                      onChange={(e) => setUserFormData(prev => ({ ...prev, admin: e.target.checked }))}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="admin" className="ml-2 text-sm font-medium text-gray-700">
                      Admin privileges
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="blocked"
                      checked={userFormData.blocked}
                      onChange={(e) => setUserFormData(prev => ({ ...prev, blocked: e.target.checked }))}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <label htmlFor="blocked" className="ml-2 text-sm font-medium text-gray-700">
                      Block user
                    </label>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Admin notes
                    </label>
                    <textarea
                      value={userFormData.notes}
                      onChange={(e) => setUserFormData(prev => ({ ...prev, notes: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Internal notes about this user..."
                    />
                  </div>
                </div>
                
                <div className="flex gap-2 mt-6">
                  <Button
                    onClick={handleUpdateUser}
                    className="flex-1"
                  >
                    Update User
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowUserModal(false)
                      setSelectedUser(null)
                      setUserFormData({ admin: false, blocked: false, notes: '' })
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      </main>
    </div>
  )
}