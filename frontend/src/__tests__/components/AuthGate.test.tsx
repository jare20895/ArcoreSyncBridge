import { render, screen, waitFor } from '@testing-library/react'

import { AuthGate } from '@/components/auth/AuthGate'

const replace = jest.fn()

jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/components/auth/AuthProvider', () => ({
  useAuth: jest.fn(),
}))

const { useRouter } = jest.requireMock('next/router') as { useRouter: jest.Mock }
const { useAuth } = jest.requireMock('@/components/auth/AuthProvider') as { useAuth: jest.Mock }

describe('AuthGate', () => {
  beforeEach(() => {
    replace.mockReset()
  })

  it('redirects unauthenticated users to login for protected routes', async () => {
    useRouter.mockReturnValue({
      pathname: '/governance',
      asPath: '/governance?tab=users',
      replace,
    })
    useAuth.mockReturnValue({
      loading: false,
      principal: null,
      requiresLogin: true,
      error: null,
    })

    render(
      <AuthGate>
        <div>Protected Content</div>
      </AuthGate>,
    )

    expect(screen.getByText('Loading authentication')).toBeInTheDocument()
    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith('/login?next=%2Fgovernance%3Ftab%3Dusers')
    })
  })

  it('renders children on the login route without redirecting', () => {
    useRouter.mockReturnValue({
      pathname: '/login',
      asPath: '/login',
      replace,
    })
    useAuth.mockReturnValue({
      loading: false,
      principal: null,
      requiresLogin: true,
      error: null,
    })

    render(
      <AuthGate>
        <div>Login Content</div>
      </AuthGate>,
    )

    expect(screen.getByText('Login Content')).toBeInTheDocument()
    expect(replace).not.toHaveBeenCalled()
  })
})
