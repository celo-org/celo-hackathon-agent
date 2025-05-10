
import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Loader } from "lucide-react";

export const LoadingReport = ({ repoName = "Repository" }: { repoName?: string }) => {
  return (
    <div className="space-y-8">
      {/* Report Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Analyzing {repoName}</h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant="outline">Repository Analysis</Badge>
            <span className="text-sm text-muted-foreground">{new Date().toISOString().split('T')[0]}</span>
            <span className="px-2 py-1 rounded-md text-xs font-medium bg-blue-500/10 text-blue-600">
              In Progress
            </span>
          </div>
        </div>
      </div>
      
      {/* Loading content */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="animate-spin mb-4">
              <Loader className="h-10 w-10" />
            </div>
            <h2 className="text-2xl font-semibold mb-2">Analyzing Repository</h2>
            <p className="text-muted-foreground mb-6 max-w-md">
              ShipMate is analyzing the code structure, identifying dependencies, and preparing your report.
              This may take a few minutes depending on the repository size.
            </p>
            
            <div className="w-full max-w-md space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Fetching repository files</span>
                  <span className="text-sm">Complete</span>
                </div>
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full w-full"></div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Processing code structure</span>
                  <span className="text-sm">In progress</span>
                </div>
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full w-[70%]"></div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Generating insights</span>
                  <span className="text-sm">Pending</span>
                </div>
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full w-0"></div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Finalizing report</span>
                  <span className="text-sm">Pending</span>
                </div>
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full w-0"></div>
                </div>
              </div>
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
};
