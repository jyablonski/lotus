import Link from "next/link";
import { PlusCircle, BarChart3, Calendar } from "lucide-react";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import { Logout } from "@/components/auth/LogoutButton";

export function ProfileActions() {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold text-dark-50">Quick Actions</h2>
      </CardHeader>
      <CardContent className="space-y-3">
        <Link href="/journal/create" className="block">
          <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg bg-lotus-500/20 hover:bg-lotus-500/30 transition-colors">
            <PlusCircle size={20} className="text-lotus-400" />
            <span className="text-lotus-300 font-medium">Create New Entry</span>
          </button>
        </Link>

        <Link href="/journal/home" className="block">
          <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg hover:bg-dark-700/50 transition-colors">
            <BarChart3 size={20} className="text-dark-400" />
            <span className="text-dark-200">View All Entries</span>
          </button>
        </Link>

        <Link href="/journal/calendar" className="block">
          <button className="w-full flex items-center space-x-3 p-3 text-left rounded-lg hover:bg-dark-700/50 transition-colors">
            <Calendar size={20} className="text-dark-400" />
            <span className="text-dark-200">Calendar View</span>
          </button>
        </Link>

        <hr className="my-4 border-dark-600" />

        <div className="pt-2">
          <Logout />
        </div>
      </CardContent>
    </Card>
  );
}
