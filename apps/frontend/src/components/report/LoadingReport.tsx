import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFormalDate } from "@/lib/date-utils";

interface LoadingReportProps {
  repoName?: string;
  progress?: number;
}

export function LoadingReport({
  repoName = "Repository",
  progress,
}: LoadingReportProps) {
  // Show progress percentage if valid value is provided, otherwise show indeterminate animation
  const hasProgress =
    progress !== undefined && progress >= 0 && progress <= 100;

  return (
    <div className="space-y-8">
      {/* Report Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Analyzing {repoName}</h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant="outline">Repository Analysis</Badge>
            <span className="text-sm text-muted-foreground">
              {formatFormalDate(new Date())}
            </span>
            <span className="px-2 py-1 rounded-md text-xs font-medium bg-blue-500/10 text-blue-600">
              In Progress
            </span>
          </div>
        </div>
      </div>

      {/* Loading content */}
      <Card className="border-border">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center text-center space-y-8 py-12">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Analyzing {repoName}</h2>
              <p className="text-muted-foreground">
                Please wait while we analyze the repository code...
              </p>
            </div>

            <div className="relative w-24 h-24">
              <div className="animate-pulse-ring absolute inset-0 rounded-full"></div>
              <div className="animate-pulse-ring animation-delay-1000 absolute inset-0 rounded-full"></div>
              <div className="relative flex items-center justify-center w-full h-full bg-background rounded-full">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="h-8 w-8 animate-pulse text-primary"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
                  />
                </svg>
              </div>
            </div>

            {hasProgress && (
              <div className="w-full max-w-md space-y-2">
                <Progress value={progress} className="h-2" />
                <p className="text-sm text-muted-foreground text-center">
                  {Math.round(progress)}% complete
                </p>
              </div>
            )}

            <div className="text-sm text-muted-foreground space-y-2">
              <p>This might take a few minutes...</p>
              <p>
                We're analyzing code structure, dependencies, and best
                practices.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skeleton placeholders for the report content */}
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-8 w-1/3 mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mb-6" />

          <Skeleton className="h-6 w-1/4 mb-3" />
          <Skeleton className="h-24 w-full mb-6 rounded-md" />

          <Skeleton className="h-6 w-1/4 mb-3" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    </div>
  );
}
