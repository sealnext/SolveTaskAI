import { Button } from "@/components/ui/button";
import { useLogout } from "../app/hooks/useLogout";

export function LogoutButton() {
  const { logout, isLoading, error } = useLogout();

  return (
    <>
      <Button
        onClick={logout}
        disabled={isLoading}
        variant="outline"
      >
        {isLoading ? 'Logging out...' : 'Log out'}
      </Button>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </>
  );
}