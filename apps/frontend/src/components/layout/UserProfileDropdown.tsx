import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/auth-context";
import { Github, LogOut, Settings, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

export function UserProfileDropdown() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  // Function to get user initials for avatar fallback
  const getUserInitials = () => {
    if (!user || !user.username) return "U";

    // Return the first letter of the username
    return user.username.charAt(0).toUpperCase();
  };

  // Handle logout
  const handleLogout = () => {
    logout();
    navigate("/");
  };

  // If user is not authenticated, show login button
  if (!isAuthenticated) {
    return (
      <Button variant="outline" onClick={() => navigate("/auth")}>
        Login
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage
              src="/placeholder-avatar.jpg"
              alt={user?.username || "User"}
            />
            <AvatarFallback>{getUserInitials()}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user?.username}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user?.email}
            </p>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem>
          <Link to="/reports" className="flex w-full items-center">
            <Github className="mr-2 h-4 w-4" />
            <span>My Reports</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem>
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>

        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
