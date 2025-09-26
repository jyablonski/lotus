import { ChevronLeft, ChevronRight } from 'lucide-react';

interface JournalPaginationProps {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    itemsPerPage: number;
    onPageChange: (page: number) => void;
    hasFilters?: boolean;
}

export function JournalPagination({
    currentPage,
    totalPages,
    totalItems,
    itemsPerPage,
    onPageChange,
    hasFilters = false
}: JournalPaginationProps) {
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);

    // Generate page numbers to show
    const getVisiblePages = () => {
        const delta = 2; // Show 2 pages on each side of current page
        const range = [];
        const rangeWithDots = [];

        // Always show first page
        range.push(1);

        // Add pages around current page
        for (let i = Math.max(2, currentPage - delta);
            i <= Math.min(totalPages - 1, currentPage + delta);
            i++) {
            range.push(i);
        }

        // Always show last page (if more than 1 page)
        if (totalPages > 1) {
            range.push(totalPages);
        }

        // Remove duplicates and sort
        const uniquePages = [...new Set(range)].sort((a, b) => a - b);

        // Add dots where there are gaps
        for (let i = 0; i < uniquePages.length; i++) {
            rangeWithDots.push(uniquePages[i]);

            if (uniquePages[i + 1] && uniquePages[i + 1] - uniquePages[i] > 1) {
                rangeWithDots.push('...');
            }
        }

        return rangeWithDots;
    };

    const visiblePages = getVisiblePages();

    return (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 py-6 border-t border-gray-200">
            {/* Results info */}
            <div className="text-sm text-muted-dark">
                Showing {startItem}-{endItem} of {totalItems} entries
                {hasFilters && <span className="ml-1">(filtered)</span>}
            </div>

            {/* Pagination controls */}
            <div className="flex items-center gap-2">
                {/* Previous button */}
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white"
                >
                    <ChevronLeft size={16} />
                    Previous
                </button>

                {/* Page numbers */}
                <div className="flex items-center gap-1">
                    {visiblePages.map((page, index) => (
                        <div key={index}>
                            {page === '...' ? (
                                <span className="px-3 py-2 text-sm text-muted-dark">...</span>
                            ) : (
                                <button
                                    onClick={() => onPageChange(page as number)}
                                    className={`px-3 py-2 text-sm border rounded-md min-w-[40px] ${currentPage === page
                                            ? 'bg-primary text-white border-primary'
                                            : 'border-gray-300 hover:bg-gray-50'
                                        }`}
                                >
                                    {page}
                                </button>
                            )}
                        </div>
                    ))}
                </div>

                {/* Next button */}
                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white"
                >
                    Next
                    <ChevronRight size={16} />
                </button>
            </div>
        </div>
    );
}