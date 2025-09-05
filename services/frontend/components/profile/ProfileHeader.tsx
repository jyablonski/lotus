// components/profile/ProfileHeader.tsx
import Image from 'next/image';
import { User } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

interface ProfileHeaderProps {
    name: string;
    email: string;
    image: string | null; // Add this line
    signupDate: string;
    firstEntryDate: Date | null;
}

export function ProfileHeader({ name, email, image, signupDate, firstEntryDate }: ProfileHeaderProps) {
    const formattedSignupDate = new Date(signupDate).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    const formattedFirstEntry = firstEntryDate?.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    const daysSinceSignup = Math.floor((Date.now() - new Date(signupDate).getTime()) / (1000 * 60 * 60 * 24));

    return (
        <Card>
            <CardContent className="p-6">
                <div className="flex items-center space-x-6">
                    {/* Avatar - GitHub image or placeholder */}
                    <div className="flex-shrink-0">
                        {image ? (
                            <Image
                                src={image}
                                alt={`${name}'s avatar`}
                                width={80}
                                height={80}
                                className="rounded-full"
                            />
                        ) : (
                            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                                <User size={32} className="text-blue-600" />
                            </div>
                        )}
                    </div>

                    {/* User info - rest remains the same */}
                    <div className="flex-1 min-w-0">
                        <h1 className="text-2xl font-bold text-gray-900 truncate">{name}</h1>
                        <p className="text-gray-600 mt-1">{email}</p>

                        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">Member since:</span>
                                <p className="font-medium">{formattedSignupDate}</p>
                                <p className="text-xs text-gray-400">{daysSinceSignup} days ago</p>
                            </div>

                            {firstEntryDate && (
                                <div>
                                    <span className="text-gray-500">First journal entry:</span>
                                    <p className="font-medium">{formattedFirstEntry}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
