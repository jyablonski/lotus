import { Card } from './Card';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    trend?: string;
    color?: string;
}

export const StatCard = ({ title, value, icon, trend, color = "blue" }: StatCardProps) => (
    <Card className="p-4">
        <div className="flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-gray-600">{title}</p>
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                {trend && <p className={`text-xs text-${color}-600 mt-1`}>{trend}</p>}
            </div>
            <div className={`p-2 bg-${color}-50 rounded-lg`}>
                {icon}
            </div>
        </div>
    </Card>
);