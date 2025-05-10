
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Download, Filter, Search } from "lucide-react";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";

// Mock data
const MOCK_REPORTS = [
  {
    id: "report-1",
    title: "Vision Model Analysis",
    category: "Computer Vision",
    date: "2025-04-22",
    status: "Completed"
  },
  {
    id: "report-2",
    title: "NLP Performance Report",
    category: "Natural Language Processing",
    date: "2025-04-20",
    status: "Completed"
  },
  {
    id: "report-3",
    title: "Reinforcement Learning Benchmark",
    category: "Reinforcement Learning",
    date: "2025-04-18",
    status: "In Progress"
  },
  {
    id: "report-4",
    title: "GPT-5 Model Evaluation",
    category: "Large Language Models",
    date: "2025-04-16",
    status: "Completed"
  },
  {
    id: "report-5",
    title: "Image Generation Quality Assessment",
    category: "Generative AI",
    date: "2025-04-15",
    status: "Completed"
  },
  {
    id: "report-6",
    title: "Speech Recognition Analysis",
    category: "Speech Processing",
    date: "2025-04-12",
    status: "In Progress"
  },
  {
    id: "report-7",
    title: "Transformer Architecture Analysis",
    category: "Large Language Models",
    date: "2025-04-10",
    status: "Completed"
  },
  {
    id: "report-8",
    title: "Recommendation Engine Performance",
    category: "Recommender Systems",
    date: "2025-04-05",
    status: "Failed"
  },
];

const CATEGORIES = [
  "All Categories",
  "Computer Vision",
  "Natural Language Processing",
  "Reinforcement Learning",
  "Large Language Models",
  "Generative AI",
  "Speech Processing",
  "Recommender Systems"
];

const STATUS_COLORS = {
  "Completed": "bg-green-500/10 text-green-600",
  "In Progress": "bg-blue-500/10 text-blue-600",
  "Failed": "bg-red-500/10 text-red-600"
};

const Reports = () => {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All Categories");
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  
  const filteredReports = MOCK_REPORTS.filter(report => {
    const matchesSearch = report.title.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "All Categories" || report.category === category;
    return matchesSearch && matchesCategory;
  });
  
  const handleSelectAllChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedReports(filteredReports.map(report => report.id));
    } else {
      setSelectedReports([]);
    }
  };
  
  const handleReportSelection = (reportId: string) => {
    setSelectedReports(prev => 
      prev.includes(reportId)
        ? prev.filter(id => id !== reportId)
        : [...prev, reportId]
    );
  };
  
  const handleDownloadSelected = () => {
    if (selectedReports.length === 0) {
      toast({
        title: "No reports selected",
        description: "Please select at least one report to download.",
        variant: "destructive"
      });
      return;
    }
    
    toast({
      title: "Download started",
      description: `${selectedReports.length} report(s) will be downloaded as a ZIP file.`
    });
  };

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
                        checked={selectedReports.length === filteredReports.length && filteredReports.length > 0}
                        onChange={handleSelectAllChange}
                      />
                    </TableHead>
                    <TableHead>Report Name</TableHead>
                    <TableHead className="hidden md:table-cell">Category</TableHead>
                    <TableHead className="hidden md:table-cell">Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReports.length > 0 ? (
                    filteredReports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell>
                          <Input
                            type="checkbox"
                            className="w-5 h-5"
                            checked={selectedReports.includes(report.id)}
                            onChange={() => handleReportSelection(report.id)}
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          <Link 
                            to={`/reports/${report.id}`}
                            className="hover:text-primary hover:underline"
                          >
                            {report.title}
                          </Link>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <Badge variant="outline">{report.category}</Badge>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">{report.date}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-md text-xs font-medium ${STATUS_COLORS[report.status as keyof typeof STATUS_COLORS] || ""}`}>
                            {report.status}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            asChild
                          >
                            <Link to={`/reports/${report.id}`}>
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
              Showing <strong>{filteredReports.length}</strong> of <strong>{MOCK_REPORTS.length}</strong> reports
            </div>
          </CardFooter>
        </Card>
      </div>
    </Layout>
  );
};

export default Reports;
