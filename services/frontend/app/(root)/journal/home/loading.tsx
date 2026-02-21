export default function JournalHomeLoading() {
  return (
    <div className="page-container">
      <div className="content-container">
        {/* Header skeleton */}
        <div className="mb-8">
          <div className="h-8 w-48 skeleton rounded mb-2" />
          <div className="h-4 w-32 skeleton rounded" />
        </div>

        {/* Filter skeleton */}
        <div className="flex gap-4 mb-8">
          <div className="h-10 w-64 skeleton rounded" />
          <div className="h-10 w-32 skeleton rounded" />
        </div>

        {/* Journal entries skeleton */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton-card p-6">
              <div className="flex justify-between mb-4">
                <div className="h-4 w-24 skeleton rounded" />
                <div className="h-4 w-16 skeleton rounded" />
              </div>
              <div className="space-y-2">
                <div className="h-4 w-full skeleton rounded" />
                <div className="h-4 w-3/4 skeleton rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
