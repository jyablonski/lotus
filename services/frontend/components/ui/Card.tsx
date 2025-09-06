interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export const Card = ({ children, className = "", hover = true }: CardProps) => (
    <div
        className={`
            bg-[#1a1f2e] 
            rounded-lg 
            border 
            border-slate-600 
            shadow-sm 
            ${hover ? 'hover:shadow-lg hover:border-slate-500 transition-all duration-200' : ''} 
            ${className}
        `}
        style={{
            backgroundColor: 'var(--card)',
            borderColor: 'var(--border)',
            color: 'var(--card-foreground)'
        }}
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
    <div
        className={`px-6 py-4 border-b ${className}`}
        style={{
            borderBottomColor: 'var(--border)'
        }}
    >
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