import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/salient/Button'
import { TextField } from '@/components/salient/Fields'
import { Logo } from '@/components/salient/Logo'
import { SlimLayout } from '@/components/salient/SlimLayout'

interface RegisterFormData {
  firstName: string
  lastName: string
  email: string
  password: string
  confirmPassword: string
  acceptedTerms: boolean
}

export default function RegisterPage() {
  const [formData, setFormData] = useState<RegisterFormData>({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptedTerms: false,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof RegisterFormData, string>>>({})

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof RegisterFormData, string>> = {}

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required'
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required'
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address'
    }

    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    if (!formData.acceptedTerms) {
      newErrors.acceptedTerms = 'You must accept the terms and conditions'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    // TODO: Implement registration logic
    console.log('Registration data:', formData)
  }

  const handleSocialSignup = (provider: string) => {
    // TODO: Implement social signup logic
    console.log(`Signup with ${provider}`)
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="relative flex min-h-full shrink-0 justify-center md:px-12 lg:px-0">
        {/* Main form section */}
        <div className="relative z-10 flex flex-1 flex-col bg-zinc-900 px-4 py-10 shadow-2xl sm:justify-center md:flex-none md:px-28 border-r border-zinc-800">
          <main className="mx-auto w-full max-w-md sm:px-4 md:w-96 md:max-w-sm md:px-0">
            {/* Logo */}
            <div className="flex">
              <Link to="/" aria-label="Home">
                <Logo className="h-10 w-auto" />
              </Link>
            </div>

            {/* Heading */}
            <h2 className="mt-20 text-3xl font-bold tracking-tight text-zinc-50">
              Create your account
            </h2>
            <p className="mt-3 text-sm text-zinc-400">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-semibold text-blue-500 hover:text-blue-400 transition-colors"
              >
                Sign in
              </Link>
            </p>

            {/* Social signup buttons */}
            <div className="mt-8 space-y-3">
              <button
                type="button"
                onClick={() => handleSocialSignup('google')}
                className="w-full flex items-center justify-center gap-3 rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-100 transition-colors border border-zinc-300 shadow-sm"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </button>

              <button
                type="button"
                onClick={() => handleSocialSignup('github')}
                className="w-full flex items-center justify-center gap-3 rounded-lg bg-zinc-800 px-4 py-2.5 text-sm font-semibold text-zinc-100 hover:bg-zinc-700 transition-colors border border-zinc-700 shadow-sm"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path
                    fillRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    clipRule="evenodd"
                  />
                </svg>
                Continue with GitHub
              </button>
            </div>

            {/* Divider */}
            <div className="relative mt-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-zinc-800"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-zinc-900 px-4 text-zinc-500">Or continue with email</span>
              </div>
            </div>

            {/* Registration form */}
            <form
              onSubmit={handleSubmit}
              className="mt-8 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2"
            >
              <div className="sm:col-span-1">
                <label htmlFor="firstName" className="block text-sm font-medium text-zinc-300 mb-2">
                  First name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  autoComplete="given-name"
                  required
                  value={formData.firstName}
                  onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                  className="block w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm transition-colors"
                  placeholder="John"
                />
                {errors.firstName && (
                  <p className="mt-1 text-xs text-red-400">{errors.firstName}</p>
                )}
              </div>

              <div className="sm:col-span-1">
                <label htmlFor="lastName" className="block text-sm font-medium text-zinc-300 mb-2">
                  Last name
                </label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  autoComplete="family-name"
                  required
                  value={formData.lastName}
                  onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                  className="block w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm transition-colors"
                  placeholder="Doe"
                />
                {errors.lastName && (
                  <p className="mt-1 text-xs text-red-400">{errors.lastName}</p>
                )}
              </div>

              <div className="col-span-full">
                <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-2">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="block w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm transition-colors"
                  placeholder="john@example.com"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-400">{errors.email}</p>
                )}
              </div>

              <div className="col-span-full">
                <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="block w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm transition-colors"
                  placeholder="••••••••"
                />
                {errors.password && (
                  <p className="mt-1 text-xs text-red-400">{errors.password}</p>
                )}
              </div>

              <div className="col-span-full">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-zinc-300 mb-2">
                  Confirm password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="block w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm transition-colors"
                  placeholder="••••••••"
                />
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-400">{errors.confirmPassword}</p>
                )}
              </div>

              {/* Terms and conditions checkbox */}
              <div className="col-span-full">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="acceptedTerms"
                      name="acceptedTerms"
                      type="checkbox"
                      checked={formData.acceptedTerms}
                      onChange={(e) => setFormData({ ...formData, acceptedTerms: e.target.checked })}
                      className="h-4 w-4 rounded border-zinc-700 bg-zinc-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-zinc-900 transition-colors cursor-pointer"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="acceptedTerms" className="text-zinc-400 cursor-pointer">
                      I agree to the{' '}
                      <Link to="/terms" className="font-medium text-blue-500 hover:text-blue-400">
                        Terms and Conditions
                      </Link>{' '}
                      and{' '}
                      <Link to="/privacy" className="font-medium text-blue-500 hover:text-blue-400">
                        Privacy Policy
                      </Link>
                    </label>
                  </div>
                </div>
                {errors.acceptedTerms && (
                  <p className="mt-1 text-xs text-red-400">{errors.acceptedTerms}</p>
                )}
              </div>

              {/* Submit button */}
              <div className="col-span-full">
                <button
                  type="submit"
                  className="w-full flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  Create account
                  <span aria-hidden="true" className="ml-1">&rarr;</span>
                </button>
              </div>
            </form>

            {/* Footer text */}
            <p className="mt-8 text-xs text-center text-zinc-500">
              By creating an account, you agree to receive updates and promotional emails.
              You can unsubscribe at any time.
            </p>
          </main>
        </div>

        {/* Gradient background side */}
        <div className="hidden sm:contents lg:relative lg:block lg:flex-1">
          <div className="absolute inset-0 h-full w-full bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 opacity-90">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnptMCAzNmMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnoiIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjA1Ii8+PC9nPjwvc3ZnPg==')] opacity-20"></div>
          </div>

          {/* Decorative content on the gradient side */}
          <div className="relative z-10 flex items-center justify-center h-full px-8">
            <div className="max-w-md text-white">
              <h3 className="text-3xl font-bold mb-4">
                Join thousands of creators
              </h3>
              <p className="text-lg text-white/90 mb-8">
                Create stunning video content with AI-powered tools. Start your journey today.
              </p>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold">AI-Powered Video Generation</h4>
                    <p className="text-sm text-white/80">Create professional videos in minutes</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold">Advanced Analytics</h4>
                    <p className="text-sm text-white/80">Track performance and optimize your content</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold">24/7 Support</h4>
                    <p className="text-sm text-white/80">Get help whenever you need it</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
