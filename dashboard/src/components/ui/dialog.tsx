import {
  Dialog,
  DialogBackdrop,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@ui-sdk/react/dialog";
import type { ReactNode } from "react";

export function PanelDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <Dialog open={open} onOpenChange={(next) => onOpenChange(next)}>
      <DialogBackdrop />
      <DialogContent>
        <div className="mb-4 flex items-start justify-between gap-6">
          <div className="flex flex-col gap-1">
            <DialogTitle className="text-lg font-medium">{title}</DialogTitle>
            {description ? (
              <DialogDescription className="text-sm text-muted">{description}</DialogDescription>
            ) : null}
          </div>
          <DialogClose className="rounded-md border border-line px-2 py-1 font-mono text-[11px] text-muted hover:text-fg">
            Close
          </DialogClose>
        </div>
        {children}
      </DialogContent>
    </Dialog>
  );
}
