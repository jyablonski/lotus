import { render, screen } from '@testing-library/react'
import HomePage from '@/components/HomePage'

// Mock the session hook for this test
jest.mock('next-auth/react', () => ({
    useSession: jest.fn(() => ({
        data: null,
        status: 'loading',
    })),
}))

describe('HomePage', () => {
    test('renders loading spinner when session is loading', () => {
        render(<HomePage />)
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
})