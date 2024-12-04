'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { useSession } from "next-auth/react"
import { cn } from "@/lib/utils"
import { 
  Shield, X, CreditCard, 
  KeyRound, Receipt, Wallet
} from 'lucide-react'

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { data: session, status } = useSession();
  const [activeTab, setActiveTab] = useState('billing');

  if (status === "loading" || !session) return null;

  const tabs = [
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
            {activeTab === 'billing' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between group hover:bg-muted/20 p-3 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <CreditCard className="w-5 h-5 text-muted-foreground" />
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
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 