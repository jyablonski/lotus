import { render, screen } from '@testing-library/react'
import LandingPage from '@/components/landing/LandingPage' // Note: default import now

// Mock Next.js Link component
jest.mock('next/link', () => {
    return ({ children, href }: { children: React.ReactNode; href: string }) => {
        return <a href={href}>{children}</a>
    }
})

describe('LandingPage', () => {
    test('renders main heading', () => {
        render(<LandingPage />)
        expect(screen.getByText((content, element) => {
            return element?.textContent === 'Your thoughts, organized and understood'
        })).toBeInTheDocument()
    })

    test('renders feature cards', () => {
        render(<LandingPage />)

        expect(screen.getByText('Simple Writing')).toBeInTheDocument()
        expect(screen.getByText('Daily Tracking')).toBeInTheDocument()
        expect(screen.getByText('Mood Insights')).toBeInTheDocument()
        expect(screen.getByText('Private & Secure')).toBeInTheDocument()
    })

})