import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { ROUTES } from "@/lib/routes";

interface JournalEmptyStateProps {
  hasEntries: boolean;
}

export function JournalEmptyState({ hasEntries }: JournalEmptyStateProps) {
  return (
    <Card className="text-center py-12">
      <CardContent>
        {!hasEntries ? (
          <div>
            <h3 className="text-lg font-medium text-primary-dark mb-2">
              No journal entries yet
            </h3>
            <p className="text-muted-dark mb-6">
              Start your journaling journey by creating your first entry.
            </p>
            <Link href={ROUTES.journal.create}>
              <button className="btn-primary">Create Your First Entry</button>
            </Link>
          </div>
        ) : (
          <div>
            <h3 className="text-lg font-medium text-primary-dark mb-2">
              No entries found
            </h3>
            <p className="text-muted-dark">
              Try adjusting your search or filter criteria.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
