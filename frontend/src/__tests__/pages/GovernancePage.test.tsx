import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import GovernancePage from '@/pages/governance'

jest.mock('@/services/api', () => ({
  getAuditLog: jest.fn(),
  getCurrentUser: jest.fn(),
  getManagedUsers: jest.fn(),
  updateManagedUser: jest.fn(),
}))

const {
  getAuditLog,
  getCurrentUser,
  getManagedUsers,
  updateManagedUser,
} = jest.requireMock('@/services/api') as {
  getAuditLog: jest.Mock
  getCurrentUser: jest.Mock
  getManagedUsers: jest.Mock
  updateManagedUser: jest.Mock
}

describe('GovernancePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('loads admin governance data and saves user access changes', async () => {
    getCurrentUser.mockResolvedValue({
      email: 'admin@example.com',
      role: 'platform_admin',
      auth_mode: 'jwt',
    })

    getAuditLog
      .mockResolvedValueOnce({
        data: [
          {
            id: 'audit-1',
            actor_email: 'admin@example.com',
            actor_role: 'platform_admin',
            action: 'auth.user.create',
            resource_type: 'app_user',
            resource_id: 'user-1',
            created_at: '2026-04-04T12:00:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 'audit-1',
            actor_email: 'admin@example.com',
            actor_role: 'platform_admin',
            action: 'auth.user.create',
            resource_type: 'app_user',
            resource_id: 'user-1',
            created_at: '2026-04-04T12:00:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 'audit-2',
            actor_email: 'admin@example.com',
            actor_role: 'platform_admin',
            action: 'auth.user.update',
            resource_type: 'app_user',
            resource_id: 'user-1',
            created_at: '2026-04-04T12:05:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })

    getManagedUsers
      .mockResolvedValueOnce({
        data: [
          {
            id: 'user-1',
            email: 'operator@example.com',
            display_name: 'Operator',
            role: 'viewer',
            status: 'ACTIVE',
            last_login_at: '2026-04-03T14:00:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 'user-1',
            email: 'operator@example.com',
            display_name: 'Operator',
            role: 'viewer',
            status: 'ACTIVE',
            last_login_at: '2026-04-03T14:00:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 'user-1',
            email: 'operator@example.com',
            display_name: 'Operator',
            role: 'admin',
            status: 'DISABLED',
            last_login_at: '2026-04-03T14:00:00',
          },
        ],
        meta: { total: 1, offset: 0 },
      })

    updateManagedUser.mockResolvedValue({
      id: 'user-1',
      role: 'admin',
      status: 'DISABLED',
    })

    render(<GovernancePage />)

    expect(await screen.findByText('Access Context')).toBeInTheDocument()
    expect(screen.getAllByText('admin@example.com')).toHaveLength(2)
    expect(screen.getByText('Recent Audit Activity')).toBeInTheDocument()
    expect(screen.getByDisplayValue('viewer')).toBeInTheDocument()

    await userEvent.selectOptions(screen.getByDisplayValue('viewer'), 'admin')
    await userEvent.selectOptions(screen.getByDisplayValue('ACTIVE'), 'DISABLED')
    await userEvent.click(screen.getByRole('button', { name: 'Save Access' }))

    await waitFor(() => {
      expect(updateManagedUser).toHaveBeenCalledWith('user-1', {
        role: 'admin',
        status: 'DISABLED',
      })
    })

    expect(await screen.findByText('Updated access for operator@example.com.')).toBeInTheDocument()
    expect(getAuditLog).toHaveBeenCalledTimes(3)
    expect(getManagedUsers).toHaveBeenCalledTimes(3)
  })
})
