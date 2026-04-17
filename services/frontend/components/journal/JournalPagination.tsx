import { ChevronLeft, ChevronRight } from "lucide-react";

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
  hasFilters = false,
}: JournalPaginationProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  // Build a compact page list: first page, a window of +/- `delta` around the
  // current page, last page, with "..." placeholders inserted for any gaps.
  const getVisiblePages = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];

    range.push(1);

    for (
      let i = Math.max(2, currentPage - delta);
      i <= Math.min(totalPages - 1, currentPage + delta);
      i++
    ) {
      range.push(i);
    }

    if (totalPages > 1) {
      range.push(totalPages);
    }

    const uniquePages = [...new Set(range)].sort((a, b) => a - b);

    for (let i = 0; i < uniquePages.length; i++) {
      rangeWithDots.push(uniquePages[i]);

      if (uniquePages[i + 1] && uniquePages[i + 1] - uniquePages[i] > 1) {
        rangeWithDots.push("...");
      }
    }

    return rangeWithDots;
  };

  const visiblePages = getVisiblePages();

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 py-6 border-t border-dark-600">
      <div className="text-sm text-muted-dark">
        Showing {startItem}-{endItem} of {totalItems} entries
        {hasFilters && <span className="ml-1">(filtered)</span>}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="btn-page"
        >
          <ChevronLeft size={16} />
          Previous
        </button>

        <div className="flex items-center gap-1">
          {visiblePages.map((page, index) => (
            <div key={index}>
              {page === "..." ? (
                <span className="px-3 py-2 text-sm text-muted-dark">...</span>
              ) : (
                <button
                  onClick={() => onPageChange(page as number)}
                  className={
                    currentPage === page
                      ? "btn-page-active"
                      : "btn-page-inactive"
                  }
                >
                  {page}
                </button>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="btn-page"
        >
          Next
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
