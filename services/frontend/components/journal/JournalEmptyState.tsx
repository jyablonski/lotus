import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/Card';

interface JournalEmptyStateProps {
    hasEntries: boolean;
}

export function JournalEmptyState({ hasEntries }: JournalEmptyStateProps) {
    return (
        <Card className="text-center py-12">
            <CardContent>
                {!hasEntries ? (
                    <div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No journal entries yet</h3>
                        <p className="text-gray-600 mb-6">Start your journaling journey by creating your first entry.</p>
                        <Link href="/journal/create">
                            <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
                                Create Your First Entry
                            </button>
                        </Link>
                    </div>
                ) : (
                    <div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No entries found</h3>
                        <p className="text-gray-600">Try adjusting your search or filter criteria.</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}