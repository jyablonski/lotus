import Link from 'next/link';
import { Plus } from 'lucide-react';

interface JournalHeaderProps {
    totalEntries: number;
}

export function JournalHeader({ totalEntries }: JournalHeaderProps) {
    return (
        <div className="flex justify-between items-center mb-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">My Journal</h1>
                <p className="text-gray-600 mt-2">
                    {totalEntries} {totalEntries === 1 ? 'entry' : 'entries'} total
                </p>
            </div>
            <Link href="/journal/create">
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Plus size={20} />
                    <span>New Entry</span>
                </button>
            </Link>
        </div>
    );
}