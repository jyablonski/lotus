import Link from 'next/link';
import { Plus } from 'lucide-react';

interface JournalHeaderProps {
    totalEntries: number;
    filteredCount?: number;
    hasFilters?: boolean;
    currentPage?: number;
    totalPages?: number;
}

export function JournalHeader({
    totalEntries,
    filteredCount,
    hasFilters = false,
    currentPage,
    totalPages
}: JournalHeaderProps) {
    const getSubtitleText = () => {
        if (hasFilters && filteredCount !== undefined) {
            return `${filteredCount} of ${totalEntries} ${totalEntries === 1 ? 'entry' : 'entries'} (filtered)`;
        }

        if (currentPage && totalPages && totalPages > 1) {
            return `${totalEntries} ${totalEntries === 1 ? 'entry' : 'entries'} total • Page ${currentPage} of ${totalPages}`;
        }

        return `${totalEntries} ${totalEntries === 1 ? 'entry' : 'entries'} total`;
    };

    return (
        <div className="flex justify-between items-center mb-8">
            <div>
                <h1 className="heading-1">My Journal</h1>
                <p className="text-muted-dark mt-2">
                    {getSubtitleText()}
                </p>

                {/* Optional: Show loading state or additional context */}
                {hasFilters && (
                    <p className="text-sm text-blue-600 mt-1">
                        Use pagination controls below to navigate filtered results
                    </p>
                )}
            </div>
            <Link href="/journal/create">
                <button className="btn-primary flex items-center space-x-2">
                    <Plus size={20} />
                    <span>New Entry</span>
                </button>
            </Link>
        </div>
    );
}