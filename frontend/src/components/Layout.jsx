import { Outlet } from 'react-router-dom'
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import AppSidebar from "@/components/app-sidebar"

export default function Layout() {
  return (
    <div className="min-h-screen bg-white dark:bg-black relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none animate-pulse-radial bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.25),transparent_50%)] dark:bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.15),transparent_50%)] bg-center bg-no-repeat">
      </div>
      <SidebarProvider>
        <div className="relative z-10 flex w-full">
          <AppSidebar />
          <SidebarInset className="flex flex-col h-screen bg-transparent">
            <Outlet />
          </SidebarInset>
        </div>
      </SidebarProvider>
    </div>
  )
}
