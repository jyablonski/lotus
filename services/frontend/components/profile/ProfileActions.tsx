import Link from 'next/link';
import { PlusCircle, BarChart3, Calendar } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Logout } from '@/components/auth/LogoutButton';

export function ProfileActions() {
    return (
        <Card>
            <CardHeader>
                <h2 className="text-xl font-semibold text-gray-900">Quick Actions</h2>
            </CardHeader>
            <CardContent className="space-y-3">

                <Link href="/journal/create" className="block">
                    <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors">
                        <PlusCircle size={20} className="text-blue-600" />
                        <span className="text-blue-900 font-medium">Create New Entry</span>
                    </button>
                </Link>

                <Link href="/journal/home" className="block">
                    <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg hover:bg-gray-50 transition-colors">
                        <BarChart3 size={20} className="text-gray-600" />
                        <span className="text-gray-900">View All Entries</span>
                    </button>
                </Link>

                <Link href="/journal/calendar" className="block">
                    <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg hover:bg-gray-50 transition-colors">
                        <Calendar size={20} className="text-gray-600" />
                        <span className="text-gray-900">Calendar View</span>
                    </button>
                </Link>

                <hr className="my-4" />

                <div className="pt-2">
                    <Logout />
                </div>
            </CardContent>
        </Card>
    );
}