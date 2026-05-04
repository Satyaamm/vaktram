import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";
import { AIConfigBanner } from "@/components/ai-config-banner";
import { AuthBootstrap } from "@/components/auth-bootstrap";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthBootstrap>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <Header />
          <AIConfigBanner />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </AuthBootstrap>
  );
}
