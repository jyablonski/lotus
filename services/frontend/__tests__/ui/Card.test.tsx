import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'

describe('Card Components', () => {
    test('renders Card with children', () => {
        render(
            <Card>
                <div>Test content</div>
            </Card>
        )
        expect(screen.getByText('Test content')).toBeInTheDocument()
    })

    test('renders CardHeader and CardContent', () => {
        render(
            <Card>
                <CardHeader>Header</CardHeader>
                <CardContent>Content</CardContent>
            </Card>
        )
        expect(screen.getByText('Header')).toBeInTheDocument()
        expect(screen.getByText('Content')).toBeInTheDocument()
    })
})