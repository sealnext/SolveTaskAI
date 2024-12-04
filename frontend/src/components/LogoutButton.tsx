import { Button } from "@/components/ui/button";
import { useLogout } from "../app/hooks/useLogout";
import { LogOut } from "lucide-react";

export function LogoutButton({ className, showText = true, children }) {
  const { logout, isLoading, error } = useLogout();

  if (children) {
    return children({ logout, isLoading });
  }

  return (
    <>
      <Button
        onClick={logout}
        disabled={isLoading}
        variant="ghost"
        className={className}
      >
        <LogOut className="h-4 w-4 text-muted-foreground" />
        {showText && (
          <span className="ml-2">
            {isLoading ? 'Logging out...' : 'Log out'}
          </span>
        )}
      </Button>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </>
  );
}