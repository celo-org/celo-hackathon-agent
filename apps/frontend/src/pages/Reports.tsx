import { Layout } from "@/components/layout/Layout";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import { formatFormalDate } from "@/lib/date-utils";
import { Loader, Search, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// Define the API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// API response interface
interface AnalysisTask {
  task_id: string;
  github_url: string;
  status: string;
  progress: number;
  submitted_at: string;
  error_message?: string;
  completed_at?: string;
}

interface AnalysisTaskListResponse {
  tasks: AnalysisTask[];
  total: number;
}

// Status mapping constants
const STATUS_MAPPING: Record<string, string> = {
  completed: "Completed",
  in_progress: "In Progress",
  pending: "Pending",
  failed: "Failed",
};

const STATUS_COLORS = {
  Completed: "bg-green-500/10 text-green-600",
  "In Progress": "bg-blue-500/10 text-blue-600",
  Failed: "bg-red-500/10 text-red-600",
  Pending: "bg-gray-500/10 text-gray-600",
};

const Reports = () => {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [tasks, setTasks] = useState<AnalysisTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<AnalysisTask | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch analysis tasks from API
  const fetchTasks = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<AnalysisTaskListResponse>(
        "/analysis/tasks"
      );
      setTasks(response.tasks || []);
    } catch (err) {
      console.error("Error fetching analysis tasks:", err);
      setError("Failed to load analysis tasks. Please try again later.");
      setTasks([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  // Filter tasks based on search
  const filteredTasks = tasks.filter((task) => {
    return task.github_url.toLowerCase().includes(search.toLowerCase());
  });

  const handleSelectAllChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event.target.checked) {
      setSelectedTasks(filteredTasks.map((task) => task.task_id));
    } else {
      setSelectedTasks([]);
    }
  };

  const handleTaskSelection = (taskId: string) => {
    setSelectedTasks((prev) =>
      prev.includes(taskId)
        ? prev.filter((id) => id !== taskId)
        : [...prev, taskId]
    );
  };

  // Extract repository name from GitHub URL
  const getRepoName = (githubUrl: string) => {
    try {
      const url = new URL(githubUrl);
      const pathParts = url.pathname.split("/").filter(Boolean);
      if (pathParts.length >= 2) {
        return `${pathParts[0]}/${pathParts[1]}`;
      }
      return githubUrl;
    } catch (e) {
      return githubUrl;
    }
  };

  // Handle task deletion
  const handleDeleteTask = async (task: AnalysisTask) => {
    setTaskToDelete(task);
  };

  const confirmDeleteTask = async () => {
    if (!taskToDelete) return;

    setIsDeleting(true);

    try {
      // If the task is completed, delete the report first
      if (taskToDelete.status === "completed") {
        try {
          // Use proper DELETE endpoint for reports
          await api.delete(`/reports/${taskToDelete.task_id}`);
          console.log("Report deleted successfully");
        } catch (err: unknown) {
          console.error("Error deleting report:", err);
          // If report not found (404) or method not allowed (405), we can continue with task deletion
          if (
            err &&
            typeof err === "object" &&
            "response" in err &&
            err.response &&
            typeof err.response === "object" &&
            "status" in err.response &&
            typeof err.response.status === "number" &&
            ![404, 405].includes(err.response.status)
          ) {
            toast({
              title: "Error",
              description: "Failed to delete the report. Please try again.",
              variant: "destructive",
            });
            setIsDeleting(false);
            setTaskToDelete(null);
            return;
          }
        }
      }

      // Delete the analysis task using the proper cancel endpoint
      try {
        // First try using the cancel endpoint which is actually implemented
        await api.delete(`/analysis/tasks/${taskToDelete.task_id}/cancel`);
        console.log("Analysis task canceled successfully");
      } catch (err: unknown) {
        console.error("Error canceling task:", err);
        // If the cancel endpoint fails, try the delete endpoint as fallback
        try {
          await api.delete(`/analysis/tasks/${taskToDelete.task_id}`);
          console.log("Analysis task deleted successfully");
        } catch (innerErr: unknown) {
          console.error("Error deleting task:", innerErr);
          throw innerErr; // Re-throw to be caught by the outer catch
        }
      }

      // Remove the task from the state
      setTasks((prev) =>
        prev.filter((t) => t.task_id !== taskToDelete.task_id)
      );

      toast({
        title: "Task deleted",
        description: "The analysis task has been deleted successfully.",
      });
    } catch (err) {
      console.error("Error in delete process:", err);
      toast({
        title: "Error",
        description: "Failed to delete the task. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
      setTaskToDelete(null);
    }
  };

  const cancelDeleteTask = () => {
    setTaskToDelete(null);
  };

  // Render loading state
  if (isLoading) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <h1 className="text-3xl font-bold">Analysis Tasks</h1>
          </div>

          <Card className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="flex flex-col items-center text-center space-y-4">
              <Loader className="h-10 w-10 animate-spin text-primary" />
              <p className="text-lg">Loading analysis tasks...</p>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  // Render error state
  if (error) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <h1 className="text-3xl font-bold">Analysis Tasks</h1>
          </div>

          <Card className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="flex flex-col items-center text-center space-y-4">
              <p className="text-lg text-red-500">{error}</p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  // Render empty state
  if (tasks.length === 0) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <h1 className="text-3xl font-bold">Analysis Tasks</h1>
          </div>

          <Card className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="flex flex-col items-center text-center space-y-4">
              <p className="text-lg">No analysis tasks found.</p>
              <Button asChild>
                <Link to="/">Analyze a Repository</Link>
              </Button>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="analyzer-container py-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <h1 className="text-3xl font-bold">Analysis Tasks</h1>
          <Button asChild variant="default">
            <Link to="/">Analyze New Repository</Link>
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <CardTitle>Repository Analysis Tasks</CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="search"
                    placeholder="Search repositories..."
                    className="pl-8 w-[250px]"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]">
                    <input
                      type="checkbox"
                      className="form-checkbox h-4 w-4 text-primary border-gray-300 rounded"
                      onChange={handleSelectAllChange}
                      checked={
                        selectedTasks.length > 0 &&
                        selectedTasks.length === filteredTasks.length
                      }
                    />
                  </TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Submitted Date</TableHead>
                  <TableHead>Completed Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTasks.map((task) => {
                  const formattedStatus =
                    STATUS_MAPPING[task.status] || task.status;
                  const statusColor =
                    STATUS_COLORS[formattedStatus] ||
                    "bg-gray-500/10 text-gray-600";
                  const isCompleted = task.status === "completed";

                  return (
                    <TableRow key={task.task_id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          className="form-checkbox h-4 w-4 text-primary border-gray-300 rounded"
                          checked={selectedTasks.includes(task.task_id)}
                          onChange={() => handleTaskSelection(task.task_id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {getRepoName(task.github_url)}
                        </div>
                        <div className="text-sm text-muted-foreground truncate max-w-[250px]">
                          {task.github_url}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColor}>{formattedStatus}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="w-[100px] h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${task.progress || 0}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {task.progress || 0}%
                        </div>
                      </TableCell>
                      <TableCell>
                        {task.submitted_at
                          ? formatFormalDate(new Date(task.submitted_at))
                          : "-"}
                      </TableCell>
                      <TableCell>
                        {task.completed_at
                          ? formatFormalDate(new Date(task.completed_at))
                          : "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isCompleted ? (
                            <Button variant="outline" size="sm" asChild>
                              <Link to={`/reports/${task.task_id}`}>
                                View Report
                              </Link>
                            </Button>
                          ) : (
                            <Button variant="outline" size="sm" disabled>
                              View Report
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-100"
                            onClick={() => handleDeleteTask(task)}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {filteredTasks.length} of {tasks.length} tasks
            </p>
            <Button variant="outline" size="sm" onClick={fetchTasks}>
              Refresh
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Delete Task Confirmation Dialog */}
      <AlertDialog open={!!taskToDelete} onOpenChange={cancelDeleteTask}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Analysis Task</AlertDialogTitle>
            <AlertDialogDescription>
              {taskToDelete?.status === "completed"
                ? "This will delete both the analysis task and its associated report. This action cannot be undone."
                : "Are you sure you want to delete this analysis task? This action cannot be undone."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteTask}
              disabled={isDeleting}
              className="bg-red-500 hover:bg-red-600"
            >
              {isDeleting ? (
                <>
                  <Loader className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Layout>
  );
};

export default Reports;
