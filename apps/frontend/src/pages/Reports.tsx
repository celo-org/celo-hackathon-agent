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
import axios from "axios";
import { Download, Loader, Search, Trash2 } from "lucide-react";
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
  const [bulkDeleteConfirm, setBulkDeleteConfirm] = useState(false);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

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

  // Get completed tasks from selected tasks
  const getSelectedCompletedTasks = () => {
    return tasks.filter(
      (task) =>
        selectedTasks.includes(task.task_id) && task.status === "completed"
    );
  };

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
        } catch (err: unknown) {
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
      } catch (err: unknown) {
        // If the cancel endpoint fails, try the delete endpoint as fallback
        await api.delete(`/analysis/tasks/${taskToDelete.task_id}`);
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

  // Download a single report
  const handleDownloadReport = async (taskId: string) => {
    try {
      // Use axios directly to get the raw blob data
      const response = await axios.get(
        `${API_BASE_URL}/reports/${taskId}/download`,
        {
          responseType: "blob",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      // Create a blob URL and trigger download
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "text/markdown",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      // Try to get filename from Content-Disposition header
      const contentDisposition = response.headers["content-disposition"];
      let filename = `report-${taskId}.md`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/"/g, "");
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download started",
        description: "The report has been downloaded.",
      });
    } catch (err) {
      console.error("Error downloading report:", err);
      toast({
        title: "Error",
        description: "Failed to download the report. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Handle bulk download of selected reports
  const handleBulkDownload = async () => {
    const completedTasks = getSelectedCompletedTasks();

    if (completedTasks.length === 0) {
      toast({
        title: "No completed tasks selected",
        description: "Please select at least one completed task to download.",
        variant: "destructive",
      });
      return;
    }

    // If only one task is selected, download it directly
    if (completedTasks.length === 1) {
      handleDownloadReport(completedTasks[0].task_id);
      return;
    }

    try {
      // Extract the task IDs for the bulk download request
      const taskIds = completedTasks.map((task) => task.task_id);

      // Make a request to the bulk download endpoint using axios
      const response = await axios.post(
        `${API_BASE_URL}/reports/download-batch`,
        { task_ids: taskIds },
        {
          responseType: "blob",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
            "Content-Type": "application/json",
          },
        }
      );

      // Create a blob URL and trigger download
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/zip",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      // Try to get filename from Content-Disposition header
      const contentDisposition = response.headers["content-disposition"];
      let filename = `reports-batch-${new Date()
        .toISOString()
        .slice(0, 10)}.zip`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/"/g, "");
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download complete",
        description: `${taskIds.length} reports have been downloaded as a zip file.`,
      });
    } catch (err) {
      console.error("Error in bulk download:", err);

      // Fallback: download reports individually if bulk endpoint fails or doesn't exist
      toast({
        title: "Bulk download failed",
        description: "Downloading reports individually instead...",
      });

      // Download files one by one with slight delay
      completedTasks.forEach((task, index) => {
        setTimeout(() => {
          handleDownloadReport(task.task_id);
        }, index * 300);
      });
    }
  };

  // Handle bulk deletion of selected reports
  const confirmBulkDelete = async () => {
    const selectedCompletedTasks = getSelectedCompletedTasks();

    if (selectedCompletedTasks.length === 0) {
      toast({
        title: "No completed tasks selected",
        description: "Please select at least one completed task to delete.",
        variant: "destructive",
      });
      setBulkDeleteConfirm(false);
      return;
    }

    setIsBulkDeleting(true);

    try {
      let successCount = 0;
      let failCount = 0;

      // Process each task sequentially
      for (const task of selectedCompletedTasks) {
        try {
          // Delete report first
          try {
            await api.delete(`/reports/${task.task_id}`);
          } catch (err: unknown) {
            // Continue if error is 404 or 405
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
              throw err; // Re-throw non-404/405 errors
            }
          }

          // Then delete task
          try {
            await api.delete(`/analysis/tasks/${task.task_id}/cancel`);
          } catch (err) {
            // Try fallback
            await api.delete(`/analysis/tasks/${task.task_id}`);
          }

          successCount++;
        } catch (err) {
          console.error(`Error deleting task ${task.task_id}:`, err);
          failCount++;
        }
      }

      // Update UI
      if (successCount > 0) {
        // Remove deleted tasks from state
        const deletedTaskIds = selectedCompletedTasks
          .filter((_, index) => index < successCount)
          .map((task) => task.task_id);

        setTasks((prev) =>
          prev.filter((t) => !deletedTaskIds.includes(t.task_id))
        );
        setSelectedTasks((prev) =>
          prev.filter((id) => !deletedTaskIds.includes(id))
        );
      }

      // Show toast with results
      if (failCount === 0) {
        toast({
          title: "Tasks deleted",
          description: `Successfully deleted ${successCount} tasks.`,
        });
      } else {
        toast({
          title: "Partial success",
          description: `Deleted ${successCount} tasks, but failed to delete ${failCount} tasks.`,
          variant: "destructive",
        });
      }
    } catch (err) {
      console.error("Error in bulk delete process:", err);
      toast({
        title: "Error",
        description: "Failed to delete the selected tasks. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsBulkDeleting(false);
      setBulkDeleteConfirm(false);
    }
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

  const selectedCompletedTasks = getSelectedCompletedTasks();

  return (
    <Layout>
      <div className="analyzer-container py-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <h1 className="text-3xl font-bold">Analysis Tasks</h1>
          <div className="flex flex-wrap gap-2">
            {selectedTasks.length > 0 && (
              <>
                <Button
                  variant="outline"
                  onClick={handleBulkDownload}
                  disabled={selectedCompletedTasks.length === 0}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Selected ({selectedCompletedTasks.length})
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setBulkDeleteConfirm(true)}
                  disabled={selectedCompletedTasks.length === 0}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Selected ({selectedCompletedTasks.length})
                </Button>
              </>
            )}
            <Button asChild variant="default">
              <Link to="/">Analyze New Repository</Link>
            </Button>
          </div>
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
                        <Link to={`/reports/${task.task_id}`}>
                          <div className="font-medium">
                            {getRepoName(task.github_url)}
                          </div>
                          <div className="text-sm text-muted-foreground truncate max-w-[250px]">
                            {task.github_url}
                          </div>
                        </Link>
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
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isCompleted ? (
                            <>
                              <Button variant="outline" size="sm" asChild>
                                <Link to={`/reports/${task.task_id}`}>
                                  View Report
                                </Link>
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-blue-500 hover:text-blue-600 hover:bg-blue-50"
                                onClick={() =>
                                  handleDownloadReport(task.task_id)
                                }
                              >
                                <Download className="h-4 w-4" />
                                <span className="sr-only">Download</span>
                              </Button>
                            </>
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

      {/* Bulk Delete Confirmation Dialog */}
      <AlertDialog open={bulkDeleteConfirm} onOpenChange={setBulkDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Selected Tasks</AlertDialogTitle>
            <AlertDialogDescription>
              This will delete {selectedCompletedTasks.length} analysis tasks
              and their associated reports. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isBulkDeleting}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmBulkDelete}
              disabled={isBulkDeleting}
              className="bg-red-500 hover:bg-red-600"
            >
              {isBulkDeleting ? (
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
