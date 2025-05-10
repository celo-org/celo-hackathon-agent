
import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LogIn, Menu } from "lucide-react";
import { useIsMobile } from "@/hooks/use-mobile";
import { 
  Sheet,
  SheetContent,
  SheetTrigger
} from "@/components/ui/sheet";

export function Navbar() {
  const isMobile = useIsMobile();
  
  return (
    <header className="border-b border-border bg-background sticky top-0 z-40">
      <div className="analyzer-container flex h-16 items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl" aria-hidden="true">🚢</span>
            <span className="font-bold text-xl text-foreground">
              ShipMate
            </span>
          </Link>
        </div>
        
        {isMobile ? (
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-foreground hover:bg-secondary">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent className="bg-card border-border">
              <div className="flex flex-col gap-4 pt-10">
                <Link to="/" className="text-lg font-medium text-foreground hover:text-primary/80 transition-colors">Home</Link>
                <Link to="/reports" className="text-lg font-medium text-foreground hover:text-primary/80 transition-colors">Reports</Link>
                <Link to="/auth" className="text-lg font-medium text-foreground hover:text-primary/80 transition-colors">Sign In</Link>
              </div>
            </SheetContent>
          </Sheet>
        ) : (
          <nav className="flex items-center gap-6">
            <Link 
              to="/" 
              className="text-sm font-medium transition-colors text-foreground/80 hover:text-primary/90"
            >
              Home
            </Link>
            <Link 
              to="/reports" 
              className="text-sm font-medium transition-colors text-foreground/80 hover:text-primary/90"
            >
              Reports
            </Link>
            <Button asChild variant="outline" className="border-border bg-secondary hover:bg-muted text-foreground">
              <Link to="/auth">
                <LogIn className="mr-2 h-4 w-4" /> Sign In
              </Link>
            </Button>
          </nav>
        )}
      </div>
    </header>
  );
}
