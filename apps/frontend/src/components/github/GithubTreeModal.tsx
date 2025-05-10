
import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { File, Folder, X, Link, Search, ChevronDown } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Checkbox } from "@/components/ui/checkbox";
import { useNavigate } from "react-router-dom";

// Mock tree data structure
interface TreeItem {
  name: string;
  path: string;
  type: "file" | "dir";
  size?: number;
  tokens?: number;
  children?: TreeItem[];
}

interface GithubTreeModalProps {
  isOpen: boolean;
  onClose: () => void;
  repoUrl: string;
}

export function GithubTreeModal({ isOpen, onClose, repoUrl }: GithubTreeModalProps) {
  const [currentPath, setCurrentPath] = useState<string>("/");
  const [expandedDirs, setExpandedDirs] = useState<string[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [totalTokens, setTotalTokens] = useState<number>(0);
  const maxTokens = 500000; // 500k token limit
  const navigate = useNavigate();
  
  // Mock data - in a real app this would come from an API call
  const mockTreeData: TreeItem[] = [
    {
      name: "src",
      path: "/src",
      type: "dir",
      children: [
        { name: "components", path: "/src/components", type: "dir", children: [
          { name: "Button.tsx", path: "/src/components/Button.tsx", type: "file", size: 2500, tokens: 625 },
          { name: "Card.tsx", path: "/src/components/Card.tsx", type: "file", size: 3200, tokens: 800 },
        ]},
        { name: "pages", path: "/src/pages", type: "dir", children: [
          { name: "index.tsx", path: "/src/pages/index.tsx", type: "file", size: 5000, tokens: 1250 },
          { name: "about.tsx", path: "/src/pages/about.tsx", type: "file", size: 3800, tokens: 950 },
        ]},
        { name: "utils.ts", path: "/src/utils.ts", type: "file", size: 1800, tokens: 450 },
      ],
    },
    {
      name: "public",
      path: "/public",
      type: "dir",
      children: [
        { name: "logo.svg", path: "/public/logo.svg", type: "file", size: 2200, tokens: 550 },
        { name: "favicon.ico", path: "/public/favicon.ico", type: "file", size: 1024, tokens: 256 },
      ],
    },
    { name: "README.md", path: "/README.md", type: "file", size: 4000, tokens: 1000 },
    { name: "package.json", path: "/package.json", type: "file", size: 2800, tokens: 700 },
  ];
  
  const toggleDir = (path: string) => {
    if (expandedDirs.includes(path)) {
      setExpandedDirs(expandedDirs.filter(dir => dir !== path));
    } else {
      setExpandedDirs([...expandedDirs, path]);
    }
  };
  
  // Helper function to get all file paths in a directory
  const getAllFilePaths = (item: TreeItem): string[] => {
    if (item.type === 'file') return [item.path];
    
    const paths: string[] = [];
    item.children?.forEach(child => {
      paths.push(...getAllFilePaths(child));
    });
    
    return paths;
  };
  
  // Helper function to check if directory has partial selection
  const hasPartialSelection = (item: TreeItem): boolean => {
    if (item.type === 'file') return false;
    
    const childPaths = getAllFilePaths(item);
    const selectedChildPaths = childPaths.filter(path => selectedItems.includes(path));
    
    return selectedChildPaths.length > 0 && selectedChildPaths.length < childPaths.length;
  };
  
  // Helper function to check if directory is fully selected
  const isFullySelected = (item: TreeItem): boolean => {
    if (item.type === 'file') return selectedItems.includes(item.path);
    
    const childPaths = getAllFilePaths(item);
    const selectedChildPaths = childPaths.filter(path => selectedItems.includes(path));
    
    return childPaths.length > 0 && selectedChildPaths.length === childPaths.length;
  };
  
  // Function to calculate total tokens for an item (file or directory)
  const calculateItemTokens = (item: TreeItem): number => {
    if (item.type === 'file') return item.tokens || 0;
    
    let total = 0;
    item.children?.forEach(child => {
      total += calculateItemTokens(child);
    });
    
    return total;
  };
  
  const toggleSelection = (item: TreeItem) => {
    const isSelected = item.type === 'file' ? 
      selectedItems.includes(item.path) : 
      isFullySelected(item);
    
    // If it's a file
    if (item.type === 'file') {
      if (isSelected) {
        // Remove from selection
        setSelectedItems(selectedItems.filter(path => path !== item.path));
        setTotalTokens(totalTokens - (item.tokens || 0));
      } else {
        // Check if adding this would exceed token limit
        if (totalTokens + (item.tokens || 0) > maxTokens) {
          toast.error("Selection would exceed the token limit of 500K");
          return;
        }
        
        // Add to selection
        setSelectedItems([...selectedItems, item.path]);
        setTotalTokens(totalTokens + (item.tokens || 0));
      }
    } 
    // If it's a directory
    else {
      const childPaths = getAllFilePaths(item);
      const itemTokens = calculateItemTokens(item);
      
      if (isSelected) {
        // Remove all child paths from selection
        setSelectedItems(selectedItems.filter(path => !childPaths.includes(path)));
        
        // Update token count by subtracting all selected child tokens
        const selectedChildPaths = childPaths.filter(path => selectedItems.includes(path));
        const selectedChildTokens = selectedChildPaths.reduce((total, path) => {
          const pathParts = path.split('/');
          const fileName = pathParts[pathParts.length - 1];
          
          const findItem = (items: TreeItem[], targetPath: string): TreeItem | undefined => {
            for (const item of items) {
              if (item.path === targetPath) return item;
              if (item.children) {
                const found = findItem(item.children, targetPath);
                if (found) return found;
              }
            }
            return undefined;
          };
          
          const fileItem = findItem(mockTreeData, path);
          return total + (fileItem?.tokens || 0);
        }, 0);
        
        setTotalTokens(totalTokens - selectedChildTokens);
      } else {
        // Check if adding all children would exceed token limit
        if (totalTokens + itemTokens > maxTokens) {
          toast.error("Selection would exceed the token limit of 500K");
          return;
        }
        
        // Add all child paths to selection
        setSelectedItems([...selectedItems, ...childPaths]);
        setTotalTokens(totalTokens + itemTokens);
      }
    }
  };
  
  // Get repository name from URL
  const repoName = repoUrl ? repoUrl.split('/').pop() : "Repository";
  
  // Function to handle adding the selected files and redirecting
  const handleAddFiles = () => {
    if (selectedItems.length === 0) {
      toast.error("Please select at least one file to analyze");
      return;
    }
    
    // Close the modal
    onClose();
    
    // Generate a unique report ID - in a real app, this would come from the server
    const reportId = `report-${Date.now()}`;
    
    // Redirect to the report page with the ID
    navigate(`/reports/${reportId}`);
  };
  
  // Function to render the tree based on current path
  const renderTree = (items: TreeItem[]) => {
    return items.map((item) => {
      const isExpanded = expandedDirs.includes(item.path);
      const isIndeterminate = hasPartialSelection(item);
      const isChecked = item.type === 'file' ? 
        selectedItems.includes(item.path) : 
        isFullySelected(item);
      
      return (
        <div key={item.path} className="border-t border-white/10">
          <div className="flex items-center justify-between py-3 px-4">
            <div className="flex items-center space-x-3">
              {/* Checkbox */}
              <div className="flex-shrink-0">
                <Checkbox
                  checked={isChecked}
                  data-state={isIndeterminate ? "indeterminate" : isChecked ? "checked" : "unchecked"}
                  onCheckedChange={() => toggleSelection(item)}
                  className="data-[state=indeterminate]:bg-primary/30 data-[state=indeterminate]:text-primary"
                />
              </div>
              
              {/* File/Folder icon */}
              <div className="flex-shrink-0">
                {item.type === 'dir' ? 
                  <Folder className="h-4 w-4 text-foreground/70" /> : 
                  <File className="h-4 w-4 text-foreground/70" />
                }
              </div>
              
              {/* Item name */}
              <div className="flex-grow text-sm text-foreground">
                {item.type === 'dir' ? (
                  <button 
                    onClick={() => toggleDir(item.path)} 
                    className="flex items-center space-x-2 hover:text-white"
                  >
                    <span>{item.name}</span>
                    {item.children && item.children.length > 0 && (
                      <ChevronDown 
                        className={`h-4 w-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                      />
                    )}
                  </button>
                ) : (
                  <span>{item.name}</span>
                )}
              </div>
            </div>
            
            {/* Token size */}
            <div className="text-xs text-foreground/60">
              {item.type === 'dir' ? (
                <>
                  {calculateItemTokens(item) > 0 
                    ? `${Math.round((calculateItemTokens(item) / 1000) * 10) / 10}%` 
                    : '<1%'}
                </>
              ) : (
                <>{item.tokens && item.tokens > 0 
                  ? `${Math.round((item.tokens / maxTokens * 100) * 10) / 10}%` 
                  : '<1%'}</>
              )}
            </div>
          </div>
          
          {/* Render children if expanded */}
          {isExpanded && item.children && (
            <div className="pl-6 border-l border-white/10">
              {renderTree(item.children)}
            </div>
          )}
        </div>
      );
    });
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] flex flex-col bg-black border-white/10 p-0">
        <DialogHeader className="px-6 pt-5 pb-2">
          <DialogTitle className="text-xl font-normal">
            Add content from GitHub
          </DialogTitle>
        </DialogHeader>

        <div className="px-6 pb-3">
          <p className="text-sm text-foreground/70">
            Select the files you would like to add to this chat
          </p>
        </div>
        
        {/* Repository URL display */}
        <div className="flex items-center gap-2 mx-6 p-3 bg-background/30 rounded-md border border-white/10">
          <div className="flex items-center gap-2 flex-1">
            {/* GitHub icon */}
            <div className="h-6 w-6 rounded-full bg-white text-black flex items-center justify-center">
              <span className="text-xs">GH</span>
            </div>
            
            {/* Repo path */}
            <div className="flex items-center gap-1">
              <span className="text-sm text-foreground/70">lomen-org /</span>
              <span className="text-sm text-foreground flex items-center gap-1">
                {repoName}
                <ChevronDown className="h-4 w-4" />
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button className="p-1.5 text-foreground/70 hover:text-foreground">
              <Link className="h-4 w-4" />
            </button>
            <button className="p-1.5 text-foreground/70 hover:text-foreground">
              <Search className="h-4 w-4" />
            </button>
          </div>
        </div>
        
        {/* File Tree */}
        <ScrollArea className="flex-grow mx-6 my-2 rounded-md">
          <div>
            {renderTree(mockTreeData)}
          </div>
        </ScrollArea>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-white/10">
          <div className="text-sm text-foreground/70">
            {selectedItems.length} {selectedItems.length === 1 ? 'file' : 'files'} selected
          </div>
          
          <div className="flex items-center gap-1">
            <Progress
              value={(totalTokens / maxTokens) * 100}
              className="w-32 h-1.5"
            />
            <span className="text-xs text-foreground/70">
              {Math.round((totalTokens / maxTokens) * 100)}% of capacity used
            </span>
          </div>
          
          <Button 
            onClick={handleAddFiles}
            className="bg-white text-black hover:bg-white/90"
            disabled={selectedItems.length === 0}
          >
            Add files
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
