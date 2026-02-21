import { Card } from "./Card";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  trendClassName?: string;
  iconContainerClassName?: string;
}

export const StatCard = ({
  title,
  value,
  icon,
  trend,
  trendClassName = "text-lotus-400",
  iconContainerClassName = "p-2 bg-lotus-500/10 rounded-lg",
}: StatCardProps) => (
  <Card className="p-4">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-dark-400">{title}</p>
        <p className="text-2xl font-bold text-dark-50">{value}</p>
        {trend && <p className={`text-xs mt-1 ${trendClassName}`}>{trend}</p>}
      </div>
      <div className={iconContainerClassName}>{icon}</div>
    </div>
  </Card>
);
