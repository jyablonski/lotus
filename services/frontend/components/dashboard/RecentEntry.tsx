import Link from 'next/link';
import { Card } from '@/components/ui/Card';

interface RecentEntryProps {
    title: string;
    date: string;
    preview: string;
    sentiment?: 'positive' | 'neutral' | 'negative';
    href: string;
}

export const RecentEntry = ({ title, date, preview, sentiment, href }: RecentEntryProps) => {
    const sentimentColors = {
        positive: 'text-green-600',
        neutral: 'text-yellow-600',
        negative: 'text-red-600'
    };

    const sentimentIcons = {
        positive: '😊',
        neutral: '😐',
        negative: '😔'
    };

    return (
        <Link href={href}>
            <Card className="p-4 cursor-pointer">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900 truncate">{title}</h3>
                    {sentiment && (
                        <span className={`text-sm ${sentimentColors[sentiment]}`}>
                            {sentimentIcons[sentiment]}
                        </span>
                    )}
                </div>
                <p className="text-xs text-gray-500 mb-2">{date}</p>
                <p className="text-sm text-gray-600 line-clamp-2">{preview}</p>
            </Card>
        </Link>
    );
};