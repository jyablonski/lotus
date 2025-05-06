import React from 'react';
import Card from './Card';

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
            <div className="flex flex-col items-center">
                <h2 className="text-2xl font-bold mt-4">{name}</h2>
                <p className="text-gray-500">{email}</p>
                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-400">Signed up on</p>
                    <p className="text-md font-medium">{formattedDate}</p>
                </div>
            </div>
        </Card>
    );
}
