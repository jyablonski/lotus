export const LoadingSpinner = () => (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex justify-center items-center">
            <div
                data-testid="loading-spinner"
                className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
            ></div>
        </div>
    </div>
);