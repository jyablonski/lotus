export default function CalendarLoading() {
  return (
    <div className="page-container">
      <div className="content-container">
        {/* Header skeleton */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="flex gap-2">
            <div className="h-10 w-10 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-10 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar grid skeleton */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              {/* Day headers */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
                  <div
                    key={i}
                    className="h-8 flex items-center justify-center text-gray-500 text-sm"
                  >
                    {day}
                  </div>
                ))}
              </div>
              {/* Calendar days */}
              <div className="grid grid-cols-7 gap-1">
                {Array.from({ length: 35 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-12 bg-gray-100 rounded animate-pulse"
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Selected date skeleton */}
          <div>
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
              <div className="space-y-3">
                <div className="h-16 bg-gray-100 rounded animate-pulse" />
                <div className="h-16 bg-gray-100 rounded animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
