import { Layout } from "@/components/layout/Layout";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";
import { Download, Filter, Loader, Search } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// Define the API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// API response interface
interface ReportSummary {
  task_id: string;
  github_url: string;
  repo_name: string;
  created_at: string;
  ipfs_hash?: string;
  published_at?: string;
  scores: Record<string, number>;
}

interface ReportsListResponse {
  reports: ReportSummary[];
  total: number;
}

// Mock data for fallback
const MOCK_REPORTS = [
  {
    id: "report-1",
    title: "Vision Model Analysis",
    category: "Computer Vision",
    date: "2025-04-22",
    status: "Completed",
  },
  {
    id: "report-2",
    title: "NLP Performance Report",
    category: "Natural Language Processing",
    date: "2025-04-20",
    status: "Completed",
  },
  {
    id: "report-3",
    title: "Reinforcement Learning Benchmark",
    category: "Reinforcement Learning",
    date: "2025-04-18",
    status: "In Progress",
  },
  {
    id: "report-4",
    title: "GPT-5 Model Evaluation",
    category: "Large Language Models",
    date: "2025-04-16",
    status: "Completed",
  },
  {
    id: "report-5",
    title: "Image Generation Quality Assessment",
    category: "Generative AI",
    date: "2025-04-15",
    status: "Completed",
  },
  {
    id: "report-6",
    title: "Speech Recognition Analysis",
    category: "Speech Processing",
    date: "2025-04-12",
    status: "In Progress",
  },
  {
    id: "report-7",
    title: "Transformer Architecture Analysis",
    category: "Large Language Models",
    date: "2025-04-10",
    status: "Completed",
  },
  {
    id: "report-8",
    title: "Recommendation Engine Performance",
    category: "Recommender Systems",
    date: "2025-04-05",
    status: "Failed",
  },
];

const CATEGORIES = ["All Categories", "Repository Analysis"];

const STATUS_MAPPING: Record<string, string> = {
  COMPLETED: "Completed",
  PROCESSING: "In Progress",
  FAILED: "Failed",
  PENDING: "Pending",
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
  const [category, setCategory] = useState("All Categories");
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch reports from API
  useEffect(() => {
    const fetchReports = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await axios.get<ReportsListResponse>(
          `${API_BASE_URL}/reports`
        );
        setReports(response.data.reports || []);
      } catch (err) {
        console.error("Error fetching reports:", err);
        setError("Failed to load reports. Please try again later.");
        // Fall back to mock data
        setReports(
          MOCK_REPORTS.map((report) => ({
            task_id: report.id,
            github_url: `https://github.com/example/${report.title
              .toLowerCase()
              .replace(/\s+/g, "-")}`,
            repo_name: report.title,
            created_at: new Date(report.date).toISOString(),
            scores: { overall: Math.floor(Math.random() * 10) + 1 },
          }))
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []);

  // Filter reports based on search and category
  const filteredReports = reports.filter((report) => {
    const matchesSearch = report.repo_name
      .toLowerCase()
      .includes(search.toLowerCase());
    // For now, simple filtering as we only have one category
    const matchesCategory = category === "All Categories";
    return matchesSearch && matchesCategory;
  });

  const handleSelectAllChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event.target.checked) {
      setSelectedReports(filteredReports.map((report) => report.task_id));
    } else {
      setSelectedReports([]);
    }
  };

  const handleReportSelection = (reportId: string) => {
    setSelectedReports((prev) =>
      prev.includes(reportId)
        ? prev.filter((id) => id !== reportId)
        : [...prev, reportId]
    );
  };

  // Handle downloading reports
  const handleDownloadSelected = async () => {
    if (selectedReports.length === 0) {
      toast({
        title: "No reports selected",
        description: "Please select at least one report to download.",
        variant: "destructive",
      });
      return;
    }

    // In a real implementation, we would batch download the reports
    // For now, just show a toast
    toast({
      title: "Download started",
      description: `${selectedReports.length} report(s) will be downloaded as a ZIP file.`,
    });
  };

  // Calculate report status based on task status
  const getReportStatus = (report: ReportSummary) => {
    // For now, we'll assume all reports are completed
    // In a real implementation, we'd check the status from the API
    return "Completed";
  };

  // Render loading state
  if (isLoading) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <h1 className="text-3xl font-bold">Project Reports</h1>
          </div>

          <Card className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="flex flex-col items-center text-center space-y-4">
              <Loader className="h-10 w-10 animate-spin text-primary" />
              <p className="text-lg">Loading reports...</p>
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
            <h1 className="text-3xl font-bold">Project Reports</h1>
          </div>

          <Card className="p-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-red-500 mb-4">
                Error Loading Reports
              </h2>
              <p className="mb-4">{error}</p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
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
          <h1 className="text-3xl font-bold">Project Reports</h1>
          {selectedReports.length > 0 && (
            <Button
              onClick={handleDownloadSelected}
              className="bg-analyzer-red hover:bg-analyzer-red/90"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Selected ({selectedReports.length})
            </Button>
          )}
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-lg">Filter Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search reports..."
                  className="pl-9"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            <div className="relative overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">
                      <Input
                        type="checkbox"
                        className="w-5 h-5"
                        checked={
                          selectedReports.length === filteredReports.length &&
                          filteredReports.length > 0
                        }
                        onChange={handleSelectAllChange}
                      />
                    </TableHead>
                    <TableHead>Repository</TableHead>
                    <TableHead className="hidden md:table-cell">
                      Score
                    </TableHead>
                    <TableHead className="hidden md:table-cell">Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReports.length > 0 ? (
                    filteredReports.map((report) => (
                      <TableRow key={report.task_id}>
                        <TableCell>
                          <Input
                            type="checkbox"
                            className="w-5 h-5"
                            checked={selectedReports.includes(report.task_id)}
                            onChange={() =>
                              handleReportSelection(report.task_id)
                            }
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          <Link
                            to={`/reports/${report.task_id}`}
                            className="hover:text-primary hover:underline"
                          >
                            {report.repo_name}
                          </Link>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {report.scores &&
                          report.scores.overall !== undefined ? (
                            <Badge variant="outline">
                              {report.scores.overall.toFixed(1)}/10
                            </Badge>
                          ) : (
                            <Badge variant="outline">N/A</Badge>
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {new Date(report.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`px-2 py-1 rounded-md text-xs font-medium ${
                              STATUS_COLORS[
                                getReportStatus(
                                  report
                                ) as keyof typeof STATUS_COLORS
                              ] || ""
                            }`}
                          >
                            {getReportStatus(report)}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="icon" asChild>
                            <Link to={`/reports/${report.task_id}`}>
                              <Download className="h-4 w-4" />
                              <span className="sr-only">Download</span>
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="h-32 text-center">
                        No reports found matching your criteria
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between border-t px-6 py-4">
            <div className="text-sm text-muted-foreground">
              Showing <strong>{filteredReports.length}</strong> of{" "}
              <strong>{reports.length}</strong> reports
            </div>
          </CardFooter>
        </Card>
      </div>
    </Layout>
  );
};

export default Reports;
