import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ApplicationsPage from '@/pages/applications'

jest.mock('@/services/api', () => ({
  getApplicationsPage: jest.fn(),
  deleteApplication: jest.fn(),
}))

jest.mock('@/components/ui/ToastProvider', () => ({
  useToast: () => ({
    showToast: jest.fn(),
  }),
}))

jest.mock('@/components/ui/ConfirmDialogProvider', () => ({
  useConfirmDialog: () => ({
    confirm: jest.fn().mockResolvedValue(true),
  }),
}))

const { getApplicationsPage } = jest.requireMock('@/services/api') as {
  getApplicationsPage: jest.Mock
}

describe('ApplicationsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('requests paginated results and advances to the next server page', async () => {
    getApplicationsPage
      .mockResolvedValueOnce({
        data: [
          {
            id: 'app-1',
            name: 'Alpha',
            owner_team: 'Platform',
            status: 'ACTIVE',
            created_at: '2026-04-01T00:00:00',
          },
        ],
        meta: { total: 25, offset: 0 },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 'app-21',
            name: 'Zulu',
            owner_team: 'Ops',
            status: 'ACTIVE',
            created_at: '2026-04-02T00:00:00',
          },
        ],
        meta: { total: 25, offset: 20 },
      })

    render(<ApplicationsPage />)

    expect(await screen.findByText('Alpha')).toBeInTheDocument()
    expect(getApplicationsPage).toHaveBeenNthCalledWith(1, {
      q: undefined,
      status: undefined,
      offset: 0,
      limit: 20,
    })
    expect(screen.getByText('Showing 1-1 of 25')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      expect(getApplicationsPage).toHaveBeenNthCalledWith(2, {
        q: undefined,
        status: undefined,
        offset: 20,
        limit: 20,
      })
    })

    expect(await screen.findByText('Zulu')).toBeInTheDocument()
    expect(screen.getByText('Showing 21-21 of 25')).toBeInTheDocument()
  })
})
