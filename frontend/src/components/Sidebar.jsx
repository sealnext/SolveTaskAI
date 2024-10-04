'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { ChevronLeft, ChevronRight, PlusCircle, Ticket, History, User, BarChart2, Settings } from 'lucide-react'
import { ProfileMenuComponent } from "@/components/profile-menu"

export function Sidebar() {
  const [sidebarState, setSidebarState] = useState('open')

  const toggleSidebar = () => {
    setSidebarState(sidebarState === 'open' ? 'closed' : 'open')
  }

  const isSidebarOpen = sidebarState === 'open'
  const isSidebarMini = sidebarState === 'mini'

  return (
    <div 
      className={`relative transition-all duration-300 ease-in-out ${
        isSidebarOpen ? 'w-64' : 'w-16'
      }`}
      onMouseEnter={() => sidebarState === 'closed' && setSidebarState('mini')}
      onMouseLeave={() => isSidebarMini && setSidebarState('closed')}
    >
      <div className={`absolute top-0 left-0 h-full overflow-hidden transition-all duration-300 ease-in-out ${
        isSidebarOpen ? 'w-64' : 'w-16'
      } bg-secondary`}>
        <div className="flex flex-col h-full">
          {/* Logo and Toggle Button */}
          <div className="p-4 flex items-center justify-between">
            {isSidebarOpen && <div className="font-bold text-xl">TicketBot</div>}
            <Button
              variant="ghost"
              size="icon"
              aria-label={isSidebarOpen ? 'Close Sidebar' : 'Open Sidebar'}
              onClick={toggleSidebar}
            >
              {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          </div>

          {/* Create New Ticket Button */}
          <Button 
            className={`m-2 flex items-center justify-${isSidebarOpen ? 'start' : 'center'}`} 
            variant="outline"
            aria-label="Create New Ticket"
          >
            <PlusCircle className="h-4 w-4" />
            {isSidebarOpen && <span className="ml-2">New Ticket</span>}
          </Button>

          {/* Navigation Items */}
          <ScrollArea className="flex-grow px-2">
            <div className="space-y-2">
            {renderNavItem('Active Tickets', <Ticket className="h-4 w-4" />, isSidebarOpen)}
              {renderNavItem('Ticket History', <History className="h-4 w-4" />, isSidebarOpen)}
              {renderNavItem('Analytics', <BarChart2 className="h-4 w-4" />, isSidebarOpen)}
            </div>

            {isSidebarOpen && (
              <>
                <Separator className="my-4" />

                {/* Recent Conversations */}
                <div>
                  <h3 className="mb-2 px-2 text-sm font-semibold">Recent Conversations</h3>
                  <div className="space-y-2">
                    {renderRecentConversations(['Ticket 1234', 'Ticket 5678'])}
                  </div>
                </div>
              </>
            )}
          </ScrollArea>

          {/* User Profile */}
          {isSidebarOpen && (
            <div className="p-4">
              <ProfileMenuComponent />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Utility function to render a navigation item.
 * 
 * @param {string} label - The label of the navigation item.
 * @param {JSX.Element} icon - The icon to be rendered with the item.
 * @param {boolean} isSidebarOpen - Boolean indicating if the sidebar is open.
 */
function renderNavItem(label, icon, isSidebarOpen) {
  return (
    <Button 
      variant="ghost" 
      className={`w-full justify-${isSidebarOpen ? 'start' : 'center'}`} 
      aria-label={label}
    >
      {icon}
      {isSidebarOpen && <span className="ml-2">{label}</span>}
    </Button>
  )
}

/**
 * Utility function to render recent conversations.
 * 
 * @param {string[]} conversations - List of recent conversations.
 */
function renderRecentConversations(conversations) {
  return conversations.map((ticket, index) => (
    <Button key={index} variant="ghost" className="w-full justify-start" aria-label={ticket}>
      <Ticket className="mr-2 h-4 w-4" />
      {ticket}
    </Button>
  ))
}