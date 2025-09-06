import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export function CreateJournalHeader() {
    return (
        <div className="mb-8">
            <Link
                href="/journal/home"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
            >
                <ArrowLeft size={20} className="mr-2" />
                Back to Journal
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Create New Entry</h1>
            <p className="text-gray-600 mt-2">
                Share your thoughts, feelings, and experiences
            </p>
        </div>
    );
}