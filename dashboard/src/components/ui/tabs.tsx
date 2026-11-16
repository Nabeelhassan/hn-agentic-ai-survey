import { Tabs, TabsList, TabsPanel, TabsTab } from "@ui-sdk/react/tabs";
import type { ReactNode } from "react";

export interface TabItem {
  value: string;
  label: string;
  content: ReactNode;
}

export function ViewTabs({
  items,
  defaultValue,
}: {
  items: TabItem[];
  defaultValue?: string;
}) {
  return (
    <Tabs defaultValue={defaultValue ?? items[0]?.value} className="flex flex-col gap-6">
      <TabsList
        aria-label="Dashboard views"
        className="flex flex-wrap gap-1 border-b border-line pb-2"
      >
        {items.map((item) => (
          <TabsTab
            key={item.value}
            value={item.value}
            className="rounded-md px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.1em] text-muted transition-colors hover:text-fg data-[selected]:bg-panel2 data-[selected]:text-accent"
          >
            {item.label}
          </TabsTab>
        ))}
      </TabsList>
      {items.map((item) => (
        <TabsPanel key={item.value} value={item.value}>
          {item.content}
        </TabsPanel>
      ))}
    </Tabs>
  );
}
