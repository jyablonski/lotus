import { render, screen } from '@testing-library/react'
import { LandingPage } from '@/components/landing/LandingPage'

describe('LandingPage', () => {
    test('renders main heading', () => {
        render(<LandingPage />)
        expect(screen.getByText((content, element) => {
            return element?.textContent === 'Your thoughts, organized and understood'
        })).toBeInTheDocument()
    })

    test('renders feature cards', () => {
        render(<LandingPage />)

        expect(screen.getByText((content, element) => {
            return element?.textContent === 'Intelligent Analysis'
        })).toBeInTheDocument()

        expect(screen.getByText((content, element) => {
            return element?.textContent === 'Secure & Private'
        })).toBeInTheDocument()

        expect(screen.getByText((content, element) => {
            return element?.textContent === 'Seamless Experience'
        })).toBeInTheDocument()
    })
})
