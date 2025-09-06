import Link from "next/link";

interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    className?: string;
}

export const NavLink = ({ href, children, className = "" }: NavLinkProps) => {
    return (
        <Link
            href={href}
            className={`
                px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200
                text-gray-200 hover:text-white hover:bg-[#1e2532]
                ${className}
            `}
        >
            {children}
        </Link>
    );
};