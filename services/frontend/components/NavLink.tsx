'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    className?: string;
}

export function NavLink({ href, children, className = "" }: NavLinkProps) {
    const pathname = usePathname();
    const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));

    return (
        <Link
            href={href}
            className={`
        font-medium transition-colors
        ${isActive
                    ? 'text-blue-600 font-semibold'
                    : 'text-gray-700 hover:text-gray-900'
                }
        ${className}
      `}
        >
            {children}
        </Link>
    );
}