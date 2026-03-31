import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Trash2Icon, Loader2 } from "lucide-react"

interface AlertDialogDestructiveProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onDelete: (id: number) => void
  itemId: number
  isDeleting: boolean
  itemType: string
}

export function AlertDialogDestructive({ onDelete, itemId, open, onOpenChange, isDeleting, itemType }: AlertDialogDestructiveProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive flex items-center justify-center w-10 h-10 rounded-full mb-2">
            <Trash2Icon className="w-5 h-5" />
          </div>
          <AlertDialogTitle>Delete {itemType}?</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete this {itemType}.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel
            onClick={() => onOpenChange(false)}
            className="cursor-pointer"
            disabled={isDeleting}
          >
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={() => onDelete(itemId)}
            className="cursor-pointer bg-destructive text-destructive-foreground hover:bg-destructive/90"
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
