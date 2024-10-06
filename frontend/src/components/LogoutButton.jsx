import { Button } from "@/components/ui/button";
import { useLogout } from "../app/hooks/useLogout";
import { LogOut } from "lucide-react";

export function LogoutButton({ className }) {
  const { logout, isLoading, error } = useLogout();

  return (
    <>
      <Button
        onClick={logout}
        disabled={isLoading}
        variant="ghost"
        className={`w-full justify-between text-left ${className}`}
      >
        <span>{isLoading ? 'Logging out...' : 'Log out'}</span>
        <LogOut className="h-4 w-4 text-gray-500" />
      </Button>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </>
  );
}