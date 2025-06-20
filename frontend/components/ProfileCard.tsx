import React from 'react';
import Card from './Card';
import { Logout } from '@/components/auth/LogoutButton';

interface ProfileCardProps {
    name?: string;
    email?: string;
    signupDate: string;
}

export function ProfileCard({ name, email, signupDate }: ProfileCardProps) {
    const formattedDate = new Date(signupDate).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    return (
        <Card>
            <div className="flex flex-col items-center space-y-6 p-6">
                <div className="text-center space-y-2">
                    <h2 className="text-2xl font-bold">{name}</h2>
                    <p className="text-gray-500">{email}</p>
                </div>

                <div className="text-center space-y-1">
                    <p className="text-sm text-gray-400">Signed up on</p>
                    <p className="text-md font-medium">{formattedDate}</p>
                </div>

                <div className="pt-4">
                    <Logout />
                </div>
            </div>
        </Card>
    );
}
