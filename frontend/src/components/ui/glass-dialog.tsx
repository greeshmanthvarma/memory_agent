import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import type { ComponentPropsWithoutRef } from "react"

type DialogProps = ComponentPropsWithoutRef<typeof Dialog>
type DialogContentProps = ComponentPropsWithoutRef<typeof DialogContent>
type DialogHeaderProps = ComponentPropsWithoutRef<typeof DialogHeader>
type DialogTitleProps = ComponentPropsWithoutRef<typeof DialogTitle>
type DialogDescriptionProps = ComponentPropsWithoutRef<typeof DialogDescription>
type DialogFooterProps = ComponentPropsWithoutRef<typeof DialogFooter>

export function GlassDialog({ open, onOpenChange, children, ...props }: DialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange} {...props}>
      {children}
    </Dialog>
  )
}

export function GlassDialogContent({ className, children, ...props }: DialogContentProps) {
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

export function GlassDialogHeader({ className, ...props }: DialogHeaderProps) {
  return <DialogHeader className={className} {...props} />
}

export function GlassDialogTitle({ className, ...props }: DialogTitleProps) {
  return <DialogTitle className={className} {...props} />
}

export function GlassDialogDescription({ className, ...props }: DialogDescriptionProps) {
  return <DialogDescription className={className} {...props} />
}

export function GlassDialogFooter({ className, ...props }: DialogFooterProps) {
  return <DialogFooter className={className} {...props} />
}
