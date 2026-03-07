import { CheckCircle } from "lucide-react";
import { CardContent } from "@/components/ui/Card";

export function SuccessMessage() {
  return (
    <div className="card" style={{ borderColor: "rgba(34, 197, 94, 0.3)" }}>
      <CardContent className="p-6 text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-400 mb-4" />
        <h3 className="text-lg font-medium text-primary-dark mb-2">
          Entry Saved Successfully!
        </h3>
        <p className="text-muted-dark">
          Your journal entry has been saved. Redirecting you back to your
          journal...
        </p>
      </CardContent>
    </div>
  );
}
