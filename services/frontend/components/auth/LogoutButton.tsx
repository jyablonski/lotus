'use client';

import { signOut } from 'next-auth/react';
import { LogOut } from 'lucide-react';

export function Logout() {
    const handleSignOut = async () => {
        await signOut({ callbackUrl: '/' });
    };

    return (
        <button
            onClick={handleSignOut}
            className="w-full flex items-center space-x-3 p-3 text-left rounded-lg hover:bg-red-50 text-red-600 hover:text-red-700 transition-colors"
        >
            <LogOut size={20} />
            <span className="font-medium">Sign Out</span>
        </button>
    );
}