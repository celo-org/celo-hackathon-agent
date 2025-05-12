import { Layout } from "@/components/layout/Layout";
import { LoadingReport } from "@/components/report/LoadingReport";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api-client";
import { ArrowLeft, Download } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

// Define the API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// API response interfaces
interface ReportResponse {
  task_id: string;
  github_url: string;
  repo_name: string;
  created_at: string;
  ipfs_hash?: string;
  published_at?: string;
  scores: Record<string, number>;
  content?: string;
}

interface AnalysisStatusResponse {
  task_id: string;
  status: string;
  github_url: string;
  progress: number;
  submitted_at: string;
  error_message?: string;
  completed_at?: string;
}

// Mock report data for fallback
const reportData = {
  "report-1": {
    title: "Vision Model Analysis",
    category: "Computer Vision",
    date: "2025-04-22",
    status: "Completed",
    content: `
# Vision Model Analysis
## Executive Summary

This report evaluates the performance of various vision models on standard benchmarks. Key findings include:

- ResNet-50 achieves 76.5% accuracy on ImageNet
- Vision Transformer (ViT) outperforms CNN architectures in most tasks
- MobileNet variants show strong performance-efficiency tradeoff
- EfficientNet remains the most parameter-efficient model class

## Model Performance

| Model | Accuracy | Parameters | FLOPs |
| ----- | -------- | ---------- | ----- |
| ResNet-50 | 76.5% | 25.6M | 4.1G |
| ViT-B/16 | 84.2% | 86.0M | 17.6G |
| MobileNetV3 | 75.8% | 5.4M | 0.58G |
| EfficientNetB0 | 77.3% | 5.3M | 0.39G |

## Analysis

The Vision Transformer architecture shows remarkable performance on various computer vision tasks despite being directly adapted from NLP applications. Its attention mechanism allows it to capture long-range dependencies that CNNs struggle with.

MobileNetV3 and EfficientNetB0 represent the current state of the art in efficient CNN architectures, with the latter being particularly well-optimized through neural architecture search.

## Recommendations

1. For mobile applications, use MobileNetV3 or EfficientNet-based architectures
2. For cloud-based applications requiring high accuracy, use Vision Transformers
3. For balanced applications, ResNet variants still provide good performance tradeoffs
4. Consider distilled models for further efficiency improvements

## Conclusion

Vision models continue to improve in both accuracy and efficiency. Transformer-based approaches represent the current leading edge, while specialized efficiency-focused architectures offer compelling alternatives for resource-constrained environments.
`,
  },
  "report-2": {
    title: "NLP Performance Report",
    category: "Natural Language Processing",
    date: "2025-04-20",
    status: "Completed",
    content: `
# NLP Performance Report
## Executive Summary

This report evaluates the performance of various NLP models on standard benchmarks. Key findings include:

- GPT-4 achieves state-of-the-art performance on most language tasks
- Smaller models like MPT-7B show promising performance for their size
- Specialized models outperform general models on domain-specific tasks
- Instruction tuning significantly improves real-world applicability

## Model Performance

| Model | MMLU | HellaSwag | TruthfulQA | Parameters |
| ----- | ---- | --------- | ---------- | ---------- |
| GPT-4 | 86.4% | 95.3% | 59.2% | ~1.8T |
| Claude 2 | 78.5% | 93.1% | 71.9% | Unknown |
| Llama 2 70B | 68.9% | 87.1% | 41.6% | 70B |
| MPT-7B | 31.2% | 76.5% | 38.9% | 7B |

## Analysis

Large language models continue to show impressive capabilities across a wide range of tasks. However, model size alone is not the only determining factor for performance. Architectural innovations, training methodology, and data quality all play significant roles.

Instruction tuning and RLHF (Reinforcement Learning from Human Feedback) have proven to be crucial for aligning model outputs with human preferences and improving their usefulness in real-world applications.

## Recommendations

1. For general-purpose applications requiring high performance, use GPT-4 or Claude 2
2. For local deployment with reasonable performance, consider Llama 2 or MPT models
3. For specialized domains, fine-tuned smaller models often outperform larger general models
4. Always evaluate models on domain-specific benchmarks rather than relying solely on general metrics

## Conclusion

The NLP landscape continues to evolve rapidly. While the largest models still hold advantages in general capabilities, the gap is narrowing as research advances. Domain-specific evaluation and customization remain essential for optimal real-world performance.
`,
  },
  "report-3": {
    title: "Reinforcement Learning Benchmark",
    category: "Reinforcement Learning",
    date: "2025-04-18",
    status: "In Progress",
    content: `
# Reinforcement Learning Benchmark
## Executive Summary

This interim report evaluates reinforcement learning algorithms on standard environments. Preliminary findings include:

- PPO consistently outperforms older algorithms like DQN
- Decision Transformer shows promising results with fewer environment interactions
- Offline RL methods are becoming increasingly practical
- Multi-agent RL remains challenging but shows progress

[Note: This report is still in progress and results are preliminary]

## Current Performance Results

| Algorithm | CartPole | LunarLander | Atari Pong | Sample Efficiency |
| --------- | -------- | ----------- | ---------- | ----------------- |
| PPO | 500.0 | 280.5 | 20.1 | Medium |
| SAC | 495.8 | 275.2 | 19.3 | High |
| DQN | 475.3 | 220.1 | 18.5 | Low |
| Decision Transformer | 485.2 | 265.8 | 19.7 | Very High |

## Preliminary Analysis

Modern policy optimization methods like PPO and SAC demonstrate strong performance across various environments. The emergence of transformer-based methods for RL is particularly notable, as they can leverage experience more efficiently.

Offline RL methods that can learn from fixed datasets without environment interaction are showing increasing promise, especially in scenarios where exploration is costly or risky.

## Next Steps

1. Complete evaluations on more complex environments
2. Add analysis of sample efficiency across algorithms
3. Include multi-agent benchmarks
4. Compare with human performance baselines

## Expected Completion

The final report is expected to be completed within 2 weeks and will include comprehensive recommendations based on full benchmark results.
`,
  },
  "report-4": {
    title: "GPT-5 Model Evaluation",
    category: "Large Language Models",
    date: "2025-04-16",
    status: "Completed",
    content: `
# GPT-5 Model Evaluation
## Executive Summary

This report evaluates the recently released GPT-5 model across various benchmarks and use cases. Key findings include:

- GPT-5 sets new state-of-the-art results across almost all language benchmarks
- Reasoning capabilities show significant improvements over GPT-4
- Hallucination rates decreased by approximately 45% compared to previous models
- Multi-modal capabilities substantially enhanced, especially for vision-language tasks

## Performance Evaluation

| Benchmark | GPT-4 | GPT-5 | Improvement |
| --------- | ----- | ----- | ----------- |
| MMLU | 86.4% | 92.1% | +5.7% |
| GSM8K | 92.0% | 97.8% | +5.8% |
| TruthfulQA | 59.2% | 78.5% | +19.3% |
| MATH | 52.9% | 68.4% | +15.5% |
| Multimodal POPE | 85.3% | 93.7% | +8.4% |

## Capability Analysis

GPT-5 demonstrates remarkable improvements in several key areas:

### Reasoning
The model shows substantially improved performance on complex reasoning tasks, including mathematical problem-solving, logical deduction, and strategic planning. Chain-of-thought reasoning appears more coherent and accurate.

### Factuality
Hallucination rates have decreased significantly, with the model more frequently expressing uncertainty rather than providing incorrect information. Citation capabilities have been enhanced.

### Multimodal Understanding
Vision-language integration is notably improved, with better understanding of complex visual scenes, diagrams, and charts. The model can reason effectively across modalities.

## Limitations

Despite improvements, some limitations persist:

1. Knowledge cutoff still presents challenges for very recent events
2. Extended reasoning beyond ~30 steps shows degradation
3. Some cultural biases remain detectable in certain contexts
4. Computational requirements have increased substantially

## Recommendations

1. GPT-5 is well-suited for complex reasoning tasks that challenged previous models
2. For factual applications, the reduced hallucination rate makes it significantly more reliable
3. Multimodal applications benefit substantially from the improved cross-modal reasoning
4. Consider computational requirements when deploying at scale

## Conclusion

GPT-5 represents a significant advancement in language model capabilities, with particularly notable improvements in reasoning, factuality, and multimodal understanding. These improvements expand the range of reliable applications for large language models.
`,
  },
  // Additional reports would be defined here
};

const ReportDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(
    null
  );
  const [pollingCount, setPollingCount] = useState(0);
  const [repoName, setRepoName] = useState("");
  const [apiReport, setApiReport] = useState<ReportResponse | null>(null);
  const [taskStatus, setTaskStatus] = useState<AnalysisStatusResponse | null>(
    null
  );
  const [mockReport, setMockReport] = useState<null | {
    title: string;
    category: string;
    date: string;
    status: string;
    content: string;
  }>(null);

  // Check if the report exists in our mock data
  const mockDataReport =
    id && id in reportData ? reportData[id as keyof typeof reportData] : null;

  // Poll the API for report status
  const pollReportStatus = async (taskId: string) => {
    try {
      // Try to get the report first
      const reportResponse = await api.get<ReportResponse>(
        `/reports/${taskId}`
      );
      setApiReport(reportResponse);
      setIsLoading(false);

      // Clear the polling interval if we got the report
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    } catch (reportError) {
      // If report isn't ready, check the task status
      try {
        const statusResponse = await api.get<AnalysisStatusResponse>(
          `/analysis/tasks/${taskId}`
        );
        setTaskStatus(statusResponse);

        // If task failed, stop polling
        if (statusResponse.status === "FAILED") {
          setIsLoading(false);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }

          toast({
            title: "Analysis failed",
            description: statusResponse.error_message || "Unknown error",
            variant: "destructive",
          });
        }
      } catch (statusError) {
        console.error("Error polling for task status:", statusError);

        // After trying 10 times, fall back to mock data
        if (pollingCount > 10) {
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }

          // Fall back to mock report after multiple failed attempts
          setMockReport({
            title: `Analysis of ${repoName}`,
            category: "Repository Analysis",
            date: new Date().toISOString().split("T")[0],
            status: "Completed",
            content: `# Repository Analysis\n\n**Repository:** ${repoName}\n\n---\n\n## Summary\n\n- This is a mock analysis report.\n- All data is generated for demonstration purposes.\n\n## Code Quality\n\n- Modular structure\n- Good use of TypeScript\n- Follows best practices\n\n## Recommendations\n\n1. Add more tests\n2. Improve documentation\n3. Refactor large components\n\n---\n\n*Generated by ShipMate AI*`,
          });
          setIsLoading(false);
        }
      }
    }
  };

  useEffect(() => {
    // Reset state when id changes
    setIsLoading(true);
    setApiReport(null);
    setTaskStatus(null);
    setMockReport(null);
    setPollingCount(0);

    // Clear any existing polling
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }

    if (!id) return;

    // Get repository name from localStorage
    setRepoName(localStorage.getItem("lastAnalyzedRepo") || "Repository");

    // If it's a mock ID or fallback to mock behavior
    if (/^report-\d+$/.test(id) && !mockDataReport) {
      // Mock polling: after 3 seconds, show a mock report
      const timeout = setTimeout(() => {
        setMockReport({
          title: `Analysis of ${repoName}`,
          category: "Repository Analysis",
          date: new Date().toISOString().split("T")[0],
          status: "Completed",
          content: `# Repository Analysis\n\n**Repository:** ${repoName}\n\n---\n\n## Summary\n\n- This is a mock analysis report.\n- All data is generated for demonstration purposes.\n\n## Code Quality\n\n- Modular structure\n- Good use of TypeScript\n- Follows best practices\n\n## Recommendations\n\n1. Add more tests\n2. Improve documentation\n3. Refactor large components\n\n---\n\n*Generated by ShipMate AI*`,
        });
        setIsLoading(false);
      }, 3000);
      return () => clearTimeout(timeout);
    } else {
      // Real API polling
      // Initial poll
      pollReportStatus(id);

      // Set up polling interval (every 3 seconds)
      const interval = setInterval(() => {
        setPollingCount((prev) => prev + 1);
        pollReportStatus(id);
      }, 3000);

      setPollingInterval(interval);

      // Clean up
      return () => {
        clearInterval(interval);
      };
    }
  }, [id]);

  const handleDownload = async () => {
    setIsDownloading(true);

    try {
      if (apiReport) {
        // For file downloads, we need to use the raw apiClient instead of our helper
        // because we need the raw response with blob data
        const response = await fetch(`${API_BASE_URL}/reports/${id}/download`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token") || ""}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to download report");
        }

        const blob = await response.blob();

        // Create a download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute(
          "download",
          `${repoName || "repository"}-analysis.md`
        );
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        toast({
          title: "Report downloaded",
          description:
            "Analysis report has been downloaded as a markdown file.",
        });
      } else {
        // Mock download for mock reports
        setTimeout(() => {
          toast({
            title: "Report downloaded",
            description:
              "Analysis report has been downloaded as a markdown file.",
          });
        }, 1500);
      }
    } catch (error) {
      console.error("Error downloading report:", error);
      toast({
        title: "Failed to download report",
        description: "Please try again or contact support.",
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  // If the report is still being generated, show the loading state
  if (isLoading) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/reports">Reports</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink>Analysis in Progress</BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <LoadingReport
            repoName={repoName}
            progress={taskStatus?.progress || 0}
          />
        </div>
      </Layout>
    );
  }

  // If we have an API report, render it
  if (apiReport) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          {/* Breadcrumbs */}
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/reports">Reports</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink>{apiReport.repo_name}</BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          {/* Report Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-bold">
                Analysis of {apiReport.repo_name}
              </h1>
              <div className="flex items-center gap-3 mt-2">
                <Badge variant="outline">Repository Analysis</Badge>
                <span className="text-sm text-muted-foreground">
                  {new Date(apiReport.created_at).toLocaleDateString()}
                </span>
                <span className="px-2 py-1 rounded-md text-xs font-medium bg-green-500/10 text-green-600">
                  Completed
                </span>
                {apiReport.scores && apiReport.scores.overall && (
                  <span className="px-2 py-1 rounded-md text-xs font-medium bg-blue-500/10 text-blue-600">
                    Score: {apiReport.scores.overall.toFixed(1)}/10
                  </span>
                )}
              </div>
            </div>
            <Button
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-white text-black hover:bg-white/90"
            >
              <Download className="mr-2 h-4 w-4" />
              {isDownloading ? "Downloading..." : "Download Report"}
            </Button>
          </div>
          {/* Report Content */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Report Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown>
                  {apiReport.content || "No content available."}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  // If a mock report is ready, render it
  if (mockReport) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          {/* Breadcrumbs */}
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/reports">Reports</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink>{mockReport.title}</BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          {/* Report Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-bold">{mockReport.title}</h1>
              <div className="flex items-center gap-3 mt-2">
                <Badge variant="outline">{mockReport.category}</Badge>
                <span className="text-sm text-muted-foreground">
                  {mockReport.date}
                </span>
                <span className="px-2 py-1 rounded-md text-xs font-medium bg-green-500/10 text-green-600">
                  {mockReport.status}
                </span>
              </div>
            </div>
            <Button
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-white text-black hover:bg-white/90"
            >
              <Download className="mr-2 h-4 w-4" />
              {isDownloading ? "Downloading..." : "Download Report"}
            </Button>
          </div>
          {/* Report Content */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Report Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown>{mockReport.content}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  // If it's a fixed mock report from reportData
  if (mockDataReport) {
    return (
      <Layout>
        <div className="analyzer-container py-10">
          {/* Breadcrumbs */}
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/reports">Reports</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink>{mockDataReport.title}</BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          {/* Report Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-bold">{mockDataReport.title}</h1>
              <div className="flex items-center gap-3 mt-2">
                <Badge variant="outline">{mockDataReport.category}</Badge>
                <span className="text-sm text-muted-foreground">
                  {mockDataReport.date}
                </span>
                <span
                  className={`px-2 py-1 rounded-md text-xs font-medium ${
                    mockDataReport.status === "Completed"
                      ? "bg-green-500/10 text-green-600"
                      : mockDataReport.status === "In Progress"
                      ? "bg-blue-500/10 text-blue-600"
                      : "bg-red-500/10 text-red-600"
                  }`}
                >
                  {mockDataReport.status}
                </span>
              </div>
            </div>

            <Button
              onClick={handleDownload}
              disabled={isDownloading || mockDataReport.status !== "Completed"}
              className="bg-white text-black hover:bg-white/90"
            >
              <Download className="mr-2 h-4 w-4" />
              {isDownloading ? "Downloading..." : "Download Report"}
            </Button>
          </div>

          {/* Report Content */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Report Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown>{mockDataReport.content}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="analyzer-container py-10">
        <h1 className="text-2xl font-bold mb-4">Report Not Found</h1>
        <p className="mb-6">
          The report you requested does not exist or has been removed.
        </p>
        <Button asChild>
          <Link to="/reports">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Reports
          </Link>
        </Button>
      </div>
    </Layout>
  );
};

export default ReportDetail;
