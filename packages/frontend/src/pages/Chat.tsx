import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useAuth } from "@/context/auth-context";
import { AnalysisTask, api, ApiError, Report } from "@/lib/api-client";
import {
  AlertCircle,
  ArrowLeft,
  BarChart3,
  CheckCircle,
  Clock,
  Code,
  ExternalLink,
  Eye,
  FileText,
  GitBranch,
  MessageSquare,
  MoreHorizontal,
  Paperclip,
  Plus,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface AnalysisCard {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick?: () => void;
}

const Chat = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  // State for main interface (when no task ID)
  const [githubUrl, setGithubUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userTasks, setUserTasks] = useState<AnalysisTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);

  // State for specific task view (when task ID provided)
  const [task, setTask] = useState<AnalysisTask | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [isLoadingTask, setIsLoadingTask] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");

  // UI state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  // UI state for analysis cards (removed from main component but kept for reference)
  const [analysisCards] = useState<AnalysisCard[]>([
    {
      id: "overview",
      title: "Project Overview",
      description: "Repository structure and purpose",
      icon: <FileText className="w-4 h-4" />,
      onClick: () => handleCardClick("overview"),
    },
    {
      id: "code-quality",
      title: "Code Quality",
      description: "Analysis of code patterns and best practices",
      icon: <Code className="w-4 h-4" />,
      onClick: () => handleCardClick("code-quality"),
    },
    {
      id: "metrics",
      title: "Key Metrics",
      description: "Performance and maintainability scores",
      icon: <BarChart3 className="w-4 h-4" />,
      onClick: () => handleCardClick("metrics"),
    },
    {
      id: "dependencies",
      title: "Dependencies",
      description: "Package analysis and security insights",
      icon: <GitBranch className="w-4 h-4" />,
      onClick: () => handleCardClick("dependencies"),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Scroll to bottom helper
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch user's tasks for sidebar
  const fetchUserTasks = async () => {
    try {
      console.log("[DEBUG] Fetching user tasks...");
      const tasksData = await api.analysis.getTasks(50); // Get more tasks for sidebar
      console.log("[DEBUG] User tasks:", tasksData);

      // Sort by submitted_at desc (newest first)
      const sortedTasks = tasksData.tasks.sort(
        (a, b) =>
          new Date(b.submitted_at).getTime() -
          new Date(a.submitted_at).getTime()
      );

      setUserTasks(sortedTasks);
    } catch (error) {
      console.error("[DEBUG] Error fetching user tasks:", error);
      toast.error("Failed to load your analyses");
    } finally {
      setIsLoadingTasks(false);
    }
  };

  // Fetch specific task data (for task view)
  const fetchTask = async () => {
    if (!id) return;

    setIsLoadingTask(true);
    try {
      console.log(`[DEBUG] Fetching task data for ID: ${id}`);
      const taskData = await api.analysis.getTask(id);
      console.log(`[DEBUG] Task data received:`, taskData);
      setTask(taskData);

      // If task is completed, fetch the report
      if (taskData.status === "completed") {
        console.log(`[DEBUG] Task completed, fetching report...`);
        try {
          const reportData = await api.reports.getReport(id);
          console.log(`[DEBUG] Report data received:`, reportData);
          setReport(reportData);
        } catch (reportError) {
          console.warn("Report not found or not ready yet:", reportError);
        }
      }

      setError(null);
    } catch (error) {
      console.error("[DEBUG] Error fetching task:", error);
      const apiError = error as ApiError;

      // If task not found (404 or 500), try to redirect to user's latest task
      if (apiError.status_code === 404 || apiError.status_code === 500) {
        console.log(
          "[DEBUG] Task not found, fetching user tasks for redirect..."
        );
        try {
          const userTasks = await api.analysis.getTasks();
          console.log("[DEBUG] User tasks for redirect:", userTasks);

          if (userTasks.tasks && userTasks.tasks.length > 0) {
            // Sort by submitted_at to get the latest task
            const sortedTasks = userTasks.tasks.sort(
              (a: AnalysisTask, b: AnalysisTask) =>
                new Date(b.submitted_at).getTime() -
                new Date(a.submitted_at).getTime()
            );

            const latestTask = sortedTasks[0];
            console.log(
              "[DEBUG] Redirecting to latest task:",
              latestTask.task_id
            );

            toast.info("Redirecting to your latest analysis", {
              description: `Task ID was invalid, showing your most recent analysis instead.`,
            });

            navigate(`/chat/${latestTask.task_id}`, { replace: true });
            return;
          }
        } catch (redirectError) {
          console.error(
            "[DEBUG] Failed to fetch user tasks for redirect:",
            redirectError
          );
        }
      }

      setError(apiError.detail || "Failed to load analysis task");
    } finally {
      setIsLoadingTask(false);
    }
  };

  // Initialize component
  useEffect(() => {
    // Always fetch user tasks for sidebar
    fetchUserTasks();

    // If we have a task ID, fetch specific task data
    if (id) {
      fetchTask();

      // Set up polling for task status
      pollingIntervalRef.current = setInterval(() => {
        fetchTask();
      }, 3000); // Poll every 3 seconds
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [id]);

  // Stop polling when task is completed or failed
  useEffect(() => {
    if (task?.status === "completed" || task?.status === "failed") {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [task?.status]);

  // Initialize welcome message when task is completed
  useEffect(() => {
    if (task?.status === "completed" && messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: "welcome",
        content: `Hello! I've completed analyzing the repository "${task.github_url}". What would you like to know about it?`,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  }, [task?.status, messages.length, task?.github_url]);

  // Handle GitHub URL submission
  const handleSubmitUrl = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!githubUrl.trim()) {
      toast.error("Please enter a GitHub URL");
      return;
    }

    // Validate GitHub URL format
    const githubUrlPattern = /^https:\/\/github\.com\/[\w\-.]+\/[\w\-.]+\/?$/;
    if (!githubUrlPattern.test(githubUrl.trim())) {
      toast.error("Please enter a valid GitHub repository URL");
      return;
    }

    setIsSubmitting(true);
    try {
      console.log("[DEBUG] Submitting analysis for URL:", githubUrl);

      const analysisData = {
        github_urls: [githubUrl.trim()],
        options: {
          analysis_type: "fast",
        },
      };

      const newTask = await api.analysis.submit(analysisData);
      console.log("[DEBUG] Analysis submitted, task:", newTask);

      toast.success("Analysis started!", {
        description: "Redirecting to analysis page...",
      });

      // Redirect to the new task
      navigate(`/chat/${newTask.task_id}`);
    } catch (error) {
      console.error("[DEBUG] Error submitting analysis:", error);
      const apiError = error as ApiError;
      toast.error("Failed to start analysis", {
        description: apiError.detail || "Please try again",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle analysis card clicks
  function handleCardClick(cardId: string) {
    if (!report?.content) {
      toast.info("Analysis not ready yet", {
        description: "Please wait for the analysis to complete.",
      });
      return;
    }

    const queries: Record<string, string> = {
      overview:
        "Give me an overview of this repository's structure and purpose.",
      "code-quality":
        "What can you tell me about the code quality and best practices?",
      metrics: "Show me the key metrics and performance insights.",
      dependencies: "Analyze the dependencies and any security concerns.",
    };

    const query = queries[cardId];
    if (query) {
      setInputMessage(query);
    }
  }

  // Handle sending chat messages
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !report?.content) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    // Simulated AI response (replace with actual API call)
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `I can help you with that question about the repository. Based on the analysis, here's what I found...\n\n*This is a simulated response. In a real implementation, this would query the AI service with the report content and user question.*`,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (id && task?.status === "completed") {
        handleSendMessage();
      }
    }
  };

  // Handle task deletion
  const handleDeleteTask = async (taskId: string) => {
    setIsDeleting(taskId);
    try {
      console.log("[DEBUG] Deleting task:", taskId);
      await api.analysis.deleteTask(taskId);

      toast.success("Analysis deleted");

      // Refresh user tasks
      await fetchUserTasks();

      // If we're currently viewing the deleted task, redirect to main chat
      if (id === taskId) {
        navigate("/chat");
      }
    } catch (error) {
      console.error("[DEBUG] Error deleting task:", error);
      const apiError = error as ApiError;
      toast.error("Failed to delete analysis", {
        description: apiError.detail || "Please try again",
      });
    } finally {
      setIsDeleting(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "in_progress":
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      case "in_progress":
        return "In Progress";
      default:
        return "Pending";
    }
  };

  const formatRepoName = (url: string) => {
    try {
      const match = url.match(/github\.com\/([^/]+)\/([^/]+)/);
      return match ? `${match[1]}/${match[2]}` : url;
    } catch {
      return url;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-80 border-r border-border bg-card/50 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Your Analyses</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/chat")}
              className="text-muted-foreground hover:text-foreground"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tasks List */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            {isLoadingTasks ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
              </div>
            ) : userTasks.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No analyses yet</p>
                <p className="text-xs">Start by analyzing a repository</p>
              </div>
            ) : (
              userTasks.map((userTask) => (
                <Card
                  key={userTask.task_id}
                  className={`p-3 cursor-pointer transition-colors hover:bg-accent/50 ${
                    id === userTask.task_id ? "bg-accent border-primary" : ""
                  }`}
                  onClick={() => navigate(`/chat/${userTask.task_id}`)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {formatRepoName(userTask.github_url)}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {getStatusIcon(userTask.status)}
                        <span className="text-xs text-muted-foreground">
                          {getStatusText(userTask.status)}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatTimeAgo(userTask.submitted_at)}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="w-6 h-6 p-0"
                          >
                            <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/chat/${userTask.task_id}`);
                            }}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            View Analysis
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteTask(userTask.task_id);
                            }}
                            className="text-red-600 focus:text-red-600"
                            disabled={isDeleting === userTask.task_id}
                          >
                            {isDeleting === userTask.task_id ? (
                              <div className="w-4 h-4 mr-2 border-2 border-red-600/30 border-t-red-600 rounded-full animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4 mr-2" />
                            )}
                            Delete Analysis
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {userTask.status === "in_progress" && (
                    <div className="mt-2">
                      <Progress value={userTask.progress} className="h-1" />
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {!id ? (
          // Main interface (no task selected)
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-2xl w-full text-center">
              <div className="mb-8">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-primary" />
                </div>
                <h1 className="text-3xl font-bold mb-2">
                  Analyze a Repository
                </h1>
                <p className="text-muted-foreground">
                  Enter a GitHub repository URL to get AI-powered insights about
                  code quality, architecture, and best practices.
                </p>
              </div>

              <form onSubmit={handleSubmitUrl} className="space-y-4">
                <div className="relative">
                  <Input
                    type="url"
                    placeholder="https://github.com/owner/repository"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    className="h-12 pr-24 text-center text-lg"
                    disabled={isSubmitting}
                  />
                  <Button
                    type="submit"
                    disabled={isSubmitting || !githubUrl.trim()}
                    className="absolute right-1 top-1 h-10 px-6"
                  >
                    {isSubmitting ? (
                      <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    ) : (
                      "Analyze"
                    )}
                  </Button>
                </div>

                <p className="text-xs text-muted-foreground">
                  Analysis typically takes 1-3 minutes depending on repository
                  size
                </p>
              </form>

              {userTasks.length > 0 && (
                <div className="mt-12">
                  <h3 className="text-lg font-semibold mb-4">
                    Recent Analyses
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {userTasks.slice(0, 4).map((recentTask) => (
                      <Card
                        key={recentTask.task_id}
                        className="p-4 cursor-pointer transition-colors hover:bg-accent/50"
                        onClick={() => navigate(`/chat/${recentTask.task_id}`)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-medium truncate">
                            {formatRepoName(recentTask.github_url)}
                          </p>
                          {getStatusIcon(recentTask.status)}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {formatTimeAgo(recentTask.submitted_at)}
                        </p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          // Task-specific interface
          <>
            {/* Header */}
            <div className="border-b border-border bg-card/50 p-4">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate("/chat")}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <ArrowLeft className="w-4 h-4" />
                </Button>

                {isLoadingTask ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <span className="text-sm text-muted-foreground">
                      Loading...
                    </span>
                  </div>
                ) : error ? (
                  <div className="flex items-center gap-2 text-red-500">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm">{error}</span>
                  </div>
                ) : task ? (
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <div>
                        <h3 className="font-medium">
                          {formatRepoName(task.github_url)}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {getStatusText(task.status)} •{" "}
                          {formatTimeAgo(task.submitted_at)}
                        </p>
                      </div>
                    </div>

                    {task.status === "in_progress" && (
                      <div className="flex items-center gap-2">
                        <Progress value={task.progress} className="w-32" />
                        <span className="text-sm text-muted-foreground">
                          {task.progress}%
                        </span>
                      </div>
                    )}

                    {task.github_url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        asChild
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <a
                          href={task.github_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </Button>
                    )}
                  </div>
                ) : null}
              </div>
            </div>

            {task?.status === "completed" ? (
              // Chat interface for completed tasks (no more Quick Insights sidebar)
              <div className="flex-1 flex flex-col">
                {/* Report Summary Card */}
                {report && (
                  <div className="p-4 border-b border-border">
                    <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
                      <SheetTrigger asChild>
                        <Card className="p-4 cursor-pointer hover:bg-accent/50 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <FileText className="w-5 h-5 text-primary" />
                              </div>
                              <div>
                                <h3 className="font-medium">Analysis Report</h3>
                                <p className="text-sm text-muted-foreground">
                                  View detailed analysis and insights
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="text-right">
                                <p className="text-sm font-medium">
                                  Score: {report.scores?.overall || "N/A"}/10
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Click to view details
                                </p>
                              </div>
                              <ArrowLeft className="w-4 h-4 rotate-180 text-muted-foreground" />
                            </div>
                          </div>
                        </Card>
                      </SheetTrigger>
                      <SheetContent
                        side="right"
                        className="w-[60%] sm:w-full sm:max-w-full"
                      >
                        <SheetHeader>
                          <SheetTitle className="flex items-center gap-2">
                            <FileText className="w-5 h-5" />
                            Analysis Report
                          </SheetTitle>
                        </SheetHeader>
                        <ScrollArea className="h-full pr-6 mt-6">
                          <div className="prose prose-sm max-w-none dark:prose-invert">
                            {report.content?.markdown ? (
                              <div className="whitespace-pre-wrap font-mono text-xs">
                                {report.content.markdown}
                              </div>
                            ) : (
                              <p className="text-muted-foreground">
                                No detailed report available.
                              </p>
                            )}
                          </div>
                        </ScrollArea>
                      </SheetContent>
                    </Sheet>
                  </div>
                )}

                {/* Chat Area */}
                <div className="flex-1 flex flex-col">
                  {/* Messages */}
                  <ScrollArea className="flex-1 p-4">
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex gap-3 ${
                            message.isUser ? "flex-row-reverse" : "flex-row"
                          }`}
                        >
                          <Avatar className="w-8 h-8">
                            <AvatarFallback>
                              {message.isUser
                                ? user?.username?.[0]?.toUpperCase()
                                : "AI"}
                            </AvatarFallback>
                          </Avatar>
                          <div
                            className={`max-w-2xl px-4 py-2 rounded-lg ${
                              message.isUser
                                ? "bg-primary text-primary-foreground ml-12"
                                : "bg-muted mr-12"
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap">
                              {message.content}
                            </p>
                            <p className="text-xs opacity-70 mt-1">
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                  </ScrollArea>

                  {/* Input */}
                  <div className="border-t border-border p-4">
                    <div className="flex gap-2">
                      <div className="flex-1 relative">
                        <Input
                          placeholder="Ask about this repository..."
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          onKeyPress={handleKeyPress}
                          className="pr-20"
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                          <Button variant="ghost" size="sm">
                            <Paperclip className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      <Button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim()}
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              // Loading/Progress view for non-completed tasks
              <div className="flex-1 flex flex-col items-center justify-center p-8">
                <div className="max-w-md w-full text-center">
                  {task?.status === "failed" ? (
                    <div className="space-y-4">
                      <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
                      <h3 className="text-xl font-semibold">Analysis Failed</h3>
                      <p className="text-muted-foreground">
                        {task.error_message ||
                          "The analysis could not be completed"}
                      </p>
                      <Button
                        onClick={() => navigate("/chat")}
                        variant="outline"
                      >
                        Try Another Repository
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                        <MessageSquare className="w-8 h-8 text-primary animate-pulse" />
                      </div>

                      <div>
                        <h3 className="text-xl font-semibold mb-2">
                          {task?.status === "in_progress"
                            ? "Analysis in Progress"
                            : "Analysis Queued"}
                        </h3>
                        <p className="text-muted-foreground">
                          {task?.status === "in_progress"
                            ? "We're analyzing your repository. This may take a few minutes."
                            : "Your analysis is queued and will start shortly."}
                        </p>
                      </div>

                      {task && task.progress > 0 && (
                        <div className="space-y-2">
                          <Progress value={task.progress} className="w-full" />
                          <p className="text-sm text-muted-foreground">
                            {task.progress}% complete
                          </p>
                        </div>
                      )}

                      <div className="text-sm text-muted-foreground">
                        <p>
                          Repository:{" "}
                          <span className="font-mono">
                            {task ? formatRepoName(task.github_url) : ""}
                          </span>
                        </p>
                        <p>
                          Started:{" "}
                          {task ? formatTimeAgo(task.submitted_at) : ""}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Chat;
