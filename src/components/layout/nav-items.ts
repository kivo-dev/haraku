import { Compass, Map as MapIcon, Route, Sparkles } from "lucide-react";

export const navItems = [
  { key: "map", href: "/map", icon: MapIcon },
  { key: "discover", href: "/discover", icon: Compass },
  { key: "assistant", href: "/assistant", icon: Sparkles },
  { key: "route", href: "/route", icon: Route },
] as const;
