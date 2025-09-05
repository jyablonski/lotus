interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export const Card = ({ children, className = "", hover = true }: CardProps) => (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${hover ? 'hover:shadow-md transition-shadow duration-200' : ''} ${className}`}>
        {children}
    </div>
);

export const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>
        {children}
    </div>
);

export const CardContent = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`px-6 py-4 ${className}`}>
        {children}
    </div>
);