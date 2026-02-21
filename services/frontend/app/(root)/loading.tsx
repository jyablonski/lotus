export default function DashboardLoading() {
  return (
    <div className="page-container">
      <div className="content-container">
        {/* Welcome header skeleton */}
        <div className="mb-8">
          <div className="h-10 w-72 skeleton rounded mb-2" />
          <div className="h-5 w-48 skeleton rounded" />
        </div>

        {/* Stats cards skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton-card p-4">
              <div className="h-4 w-20 skeleton rounded mb-2" />
              <div className="h-8 w-16 skeleton rounded" />
            </div>
          ))}
        </div>

        {/* Main content grid skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent entries skeleton */}
          <div className="skeleton-card p-6">
            <div className="h-6 w-32 skeleton rounded mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="border-b border-dark-600 pb-4">
                  <div className="flex justify-between mb-2">
                    <div className="h-4 w-24 skeleton rounded" />
                    <div className="h-4 w-16 skeleton rounded" />
                  </div>
                  <div className="h-4 w-full skeleton rounded" />
                </div>
              ))}
            </div>
          </div>

          {/* Mood chart skeleton */}
          <div className="skeleton-card p-6">
            <div className="h-6 w-32 skeleton rounded mb-4" />
            <div className="h-48 skeleton rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}
