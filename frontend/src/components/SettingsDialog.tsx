'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { useSession } from "next-auth/react"
import { Settings, User, Shield, X } from 'lucide-react'
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import { useTheme } from "@/contexts/ThemeContext"
import { ThemeSwitch } from "./ProfileMenu"

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { data: session, status } = useSession();
  const [activeTab, setActiveTab] = useState('general');
  const [showCode, setShowCode] = useState(false);
  const { theme, toggleTheme } = useTheme();

  if (status === "loading" || !session) return null;

  const tabs = [
    { id: 'general', icon: <Settings className="h-4 w-4" />, label: 'General' },
    { id: 'profile', icon: <User className="h-4 w-4" />, label: 'Profile' },
    { id: 'security', icon: <Shield className="h-4 w-4" />, label: 'Security' },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background p-0 rounded-2xl shadow-xl max-w-md w-full h-[600px] flex flex-col">
        {/* Header - Fixed */}
        <div className="p-4 border-b border-border/10">
          <div className="flex items-center justify-between">
            <div className="flex space-x-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors duration-200",
                    activeTab === tab.id 
                      ? "bg-accent text-accent-foreground" 
                      : "text-muted-foreground hover:bg-muted/50"
                  )}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
            <button 
              onClick={() => onOpenChange(false)} 
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              aria-label="Close"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-4">
            {activeTab === 'general' && (
              <>
                <div className="space-y-4">
                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Theme</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Select your preferred theme
                      </p>
                    </div>
                    <ThemeSwitch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Show code snippets</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Always show code when using data analyst
                      </p>
                    </div>
                    <Switch 
                      checked={showCode}
                      onCheckedChange={setShowCode}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Language</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Choose your preferred language
                      </p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      Auto-detect
                    </Button>
                  </div>
                </div>

                <div className="h-px w-full bg-border/10 my-6" />

                <div className="space-y-4">
                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Archived chats</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Manage your archived conversations
                      </p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      Manage
                    </Button>
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Archive all chats</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Archive all your current conversations
                      </p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      Archive all
                    </Button>
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div>
                      <h3 className="text-sm font-medium text-destructive">Delete all chats</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Permanently delete all conversations
                      </p>
                    </div>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      className="hover:bg-destructive/90 text-sm"
                    >
                      Delete all
                    </Button>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-4">
                <h2 className="text-lg font-medium">Profile Settings</h2>
                {/* Profile content */}
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-4">
                <h2 className="text-lg font-medium">Security Settings</h2>
                {/* Security content */}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 