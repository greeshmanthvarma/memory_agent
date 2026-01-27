import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

export function GlassDialog({ open, onOpenChange, children, className, ...props }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange} {...props}>
      {children}
    </Dialog>
  )
}

export function GlassDialogContent({ className, children, ...props }) {
  return (
    <DialogContent
      className={cn(
        "bg-white/30 dark:bg-gray-900/40 backdrop-blur-2xl",
        "border border-white/40 dark:border-white/20",
        "shadow-2xl",
        "rounded-3xl",
        className
      )}
      {...props}
    >
      {children}
    </DialogContent>
  )
}

export function GlassDialogHeader({ className, ...props }) {
  return <DialogHeader className={className} {...props} />
}

export function GlassDialogTitle({ className, ...props }) {
  return <DialogTitle className={className} {...props} />
}

export function GlassDialogDescription({ className, ...props }) {
  return <DialogDescription className={className} {...props} />
}

export function GlassDialogFooter({ className, ...props }) {
  return <DialogFooter className={className} {...props} />
}
