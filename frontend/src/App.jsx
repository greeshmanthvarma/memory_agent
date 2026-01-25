import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import {Input} from "@/components/ui/input"
import {InputGroup,InputGroupButton,InputGroupTextarea} from "@/components/ui/input-group"
import AppSidebar from "@/components/app-sidebar"
import { Send } from "lucide-react"
export default function App() {
  return (
    <div className="min-h-screen bg-white dark:bg-black relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none animate-pulse-radial bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.25),transparent_50%)] dark:bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.15),transparent_50%)] bg-center bg-no-repeat">
      </div>
      <SidebarProvider>
        <div className="relative z-10 flex">
          <AppSidebar />
          <SidebarInset className="bg-transparent">
          <div className="border-t p-4 w-[500px]">
            <InputGroup>
              <InputGroupTextarea placeholder="Ask Away!" className="rounded-full w-full"/>
              <InputGroupButton className="rounded-full">
                <Send />
              </InputGroupButton>
            </InputGroup>  
          </div>
             
            </SidebarInset>
        </div>
      </SidebarProvider>

     
    </div>
  )
}