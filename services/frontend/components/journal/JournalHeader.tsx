import Link from 'next/link';
import { Plus } from 'lucide-react';

interface JournalHeaderProps {
    totalEntries: number;
}

export function JournalHeader({ totalEntries }: JournalHeaderProps) {
    return (
        <div className="flex justify-between items-center mb-8">
            <div>
                <h1 className="heading-1">My Journal</h1>
                <p className="text-muted-dark mt-2">
                    {totalEntries} {totalEntries === 1 ? 'entry' : 'entries'} total
                </p>
            </div>
            <Link href="/journal/create">
                <button className="btn-primary flex items-center space-x-2">
                    <Plus size={20} />
                    <span>New Entry</span>
                </button>
            </Link>
        </div>
    );
}