interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export const Card = ({ children, className = "", hover = true }: CardProps) => (
    <div
        className={`
            card
            ${hover ? 'hover:shadow-lg transition-all duration-200' : ''} 
            ${className}
        `}
    >
        {children}
    </div>
);

export const CardHeader = ({
    children,
    className = ""
}: {
    children: React.ReactNode;
    className?: string
}) => (
    <div className={`px-6 py-4 border-b border-dark-600 ${className}`}>
        {children}
    </div>
);

export const CardContent = ({
    children,
    className = ""
}: {
    children: React.ReactNode;
    className?: string
}) => (
    <div className={`px-6 py-4 ${className}`}>
        {children}
    </div>
);