export default function ProfileLoading() {
  return (
    <div className="page-container">
      <div className="content-container space-y-8">
        {/* Profile header skeleton */}
        <div className="skeleton-card p-6">
          <div className="flex items-center gap-6">
            <div className="h-24 w-24 skeleton rounded-full" />
            <div className="space-y-3">
              <div className="h-8 w-48 skeleton rounded" />
              <div className="h-4 w-64 skeleton rounded" />
              <div className="h-4 w-40 skeleton rounded" />
            </div>
          </div>
        </div>

        {/* Statistics section skeleton */}
        <div>
          <div className="h-8 w-48 skeleton rounded mb-6" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="skeleton-card p-4">
                <div className="h-4 w-16 skeleton rounded mb-2" />
                <div className="h-8 w-12 skeleton rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Insights and actions skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="skeleton-card p-6">
            <div className="h-6 w-32 skeleton rounded mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-4 w-24 skeleton rounded" />
                  <div className="h-4 w-16 skeleton rounded" />
                </div>
              ))}
            </div>
          </div>
          <div className="skeleton-card p-6">
            <div className="h-6 w-32 skeleton rounded mb-4" />
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-12 skeleton rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
