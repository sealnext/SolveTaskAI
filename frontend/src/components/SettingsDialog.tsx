'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { useSession } from "next-auth/react"
import { 
  Settings, Shield, X, CreditCard, User, 
  Globe, Bell, Code, Archive, Trash2, 
  KeyRound, Mail, UserPlus, Lock,
  CreditCard as PaymentIcon, Receipt, Wallet, History
} from 'lucide-react'
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
  const [notifications, setNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  const { theme, toggleTheme } = useTheme();

  if (status === "loading" || !session) return null;

  const tabs = [
    { id: 'general', icon: <Settings className="h-4 w-4" />, label: 'General' },
    { id: 'profile', icon: <User className="h-4 w-4" />, label: 'Profile' },
    { id: 'billing', icon: <CreditCard className="h-4 w-4" />, label: 'Billing' },
    { id: 'security', icon: <Shield className="h-4 w-4" />, label: 'Security' },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background p-0 rounded-2xl shadow-xl max-w-xl w-[95vw] h-[80vh] flex flex-col fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%]">
        <div className="p-4 border-border/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Settings</h2>
            <button 
              onClick={() => onOpenChange(false)} 
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tabs - Scrollable container */}
          <div className="overflow-x-auto -mx-4 px-4">
            <div className="flex space-x-1 min-w-max">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors duration-200 whitespace-nowrap",
                    activeTab === tab.id 
                      ? "bg-accent text-accent-foreground" 
                      : "text-muted-foreground hover:bg-muted/50"
                  )}
                >
                  {tab.icon}
                  <span className="text-xs sm:text-sm">{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-4 space-y-4">
            {activeTab === 'general' && (
              <>
                <div className="space-y-4">
                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Globe className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Language</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Choose your preferred language
                        </p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      English (US)
                    </Button>
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Bell className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Notifications</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Receive chat and system notifications
                        </p>
                      </div>
                    </div>
                    <Switch 
                      checked={notifications}
                      onCheckedChange={setNotifications}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Code className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Code Snippets</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Show code snippets in chat responses
                        </p>
                      </div>
                    </div>
                    <Switch 
                      checked={showCode}
                      onCheckedChange={setShowCode}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Settings className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Auto-save chats</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Automatically save chat history
                        </p>
                      </div>
                    </div>
                    <Switch 
                      checked={autoSave}
                      onCheckedChange={setAutoSave}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>
                </div>

                <div className="h-px w-full bg-border/10 my-6" />

                <div className="space-y-4">
                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Archive className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Archived chats</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          View and restore archived conversations
                        </p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      View Archive
                    </Button>
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <History className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h3 className="text-sm font-medium text-foreground">Export History</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Download your chat history
                        </p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-border/20 hover:bg-muted/20 text-sm"
                    >
                      Export
                    </Button>
                  </div>

                  <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <Trash2 className="w-5 h-5 text-destructive" />
                      <div>
                        <h3 className="text-sm font-medium text-destructive">Clear History</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          Permanently delete all conversations
                        </p>
                      </div>
                    </div>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      className="hover:bg-destructive/90 text-sm"
                    >
                      Clear All
                    </Button>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <User className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Personal Information</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Update your personal details
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Edit
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <Mail className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Email Preferences</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Manage email notifications
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Configure
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <UserPlus className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Connected Accounts</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Manage linked accounts and services
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Manage
                  </Button>
                </div>
              </div>
            )}

            {activeTab === 'billing' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <PaymentIcon className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Payment Methods</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Manage your payment methods
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Add Method
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <Receipt className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Billing History</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        View past invoices and payments
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    View History
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <Wallet className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Subscription Plan</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Manage your subscription
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Upgrade
                  </Button>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <KeyRound className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Password</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Change your password
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Update
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Two-Factor Auth</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Enable two-factor authentication
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    Enable
                  </Button>
                </div>

                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <Lock className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">Login History</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        View recent login activity
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-border/20 hover:bg-muted/20 text-sm"
                  >
                    View
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 