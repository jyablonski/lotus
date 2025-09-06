import Link from 'next/link';
import { Card } from '@/components/ui/Card';

interface QuickActionProps {
    title: string;
    href: string;
    icon: React.ReactNode;
    description?: string;
}

export const QuickAction = ({ title, href, icon, description }: QuickActionProps) => (
    <Link href={href}>
        <Card className="p-4 h-full cursor-pointer hover:border-blue-300">
            <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                    {icon}
                </div>
                <div>
                    <h3 className="font-medium text-gray-900">{title}</h3>
                    {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
                </div>
            </div>
        </Card>
    </Link>
);