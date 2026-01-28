export default function DashboardLoading() {
  return (
    <div className="page-container">
      <div className="content-container">
        {/* Welcome header skeleton */}
        <div className="mb-8">
          <div className="h-10 w-72 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-5 w-48 bg-gray-200 rounded animate-pulse" />
        </div>

        {/* Stats cards skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="h-4 w-20 bg-gray-200 rounded animate-pulse mb-2" />
              <div className="h-8 w-16 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>

        {/* Main content grid skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent entries skeleton */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="border-b pb-4">
                  <div className="flex justify-between mb-2">
                    <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                    <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
                  </div>
                  <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
                </div>
              ))}
            </div>
          </div>

          {/* Mood chart skeleton */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="h-48 bg-gray-100 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
