import Link from "next/link";
import {
  PlusCircle,
  BarChart3,
  Calendar,
  Settings,
  Gamepad2,
} from "lucide-react";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import { Logout } from "@/components/auth/LogoutButton";
import { ROUTES } from "@/lib/routes";

interface ProfileActionsProps {
  isAdmin?: boolean;
}

export function ProfileActions({ isAdmin = false }: ProfileActionsProps) {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold text-dark-50">Quick Actions</h2>
      </CardHeader>
      <CardContent className="space-y-3">
        {isAdmin && (
          <Link href={ROUTES.profileCsgodouble} className="block">
            <button className="action-item">
              <Gamepad2 size={20} className="text-lotus-400" />
              <span className="text-lotus-300 font-medium">CSGO Double</span>
            </button>
          </Link>
        )}
        <Link href={ROUTES.journal.create} className="block">
          <button className="action-item-primary">
            <PlusCircle size={20} className="text-lotus-400" />
            <span className="text-lotus-300 font-medium">Create New Entry</span>
          </button>
        </Link>

        <Link href={ROUTES.journal.home} className="block">
          <button className="action-item">
            <BarChart3 size={20} className="text-dark-400" />
            <span className="text-dark-200">View All Entries</span>
          </button>
        </Link>

        <Link href={ROUTES.journal.calendar} className="block">
          <button className="action-item">
            <Calendar size={20} className="text-dark-400" />
            <span className="text-dark-200">Calendar View</span>
          </button>
        </Link>

        <Link href={ROUTES.profileSettings} className="block">
          <button className="action-item">
            <Settings size={20} className="text-dark-400" />
            <span className="text-dark-200">Settings</span>
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
