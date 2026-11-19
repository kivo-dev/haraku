import { BottomNav } from "@/components/layout/BottomNav";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { PaperScene } from "@/components/ui/PaperScene";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative isolate min-h-dvh overflow-x-clip bg-mist-200">
      <PaperScene />
      <SiteHeader />
      <main className="mx-auto w-full max-w-md pb-32 pt-4 md:max-w-7xl md:pb-16">{children}</main>
      <BottomNav />
    </div>
  );
}
