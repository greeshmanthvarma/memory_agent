import { useState, useEffect } from "react"
import { GlassDialog, GlassDialogContent, GlassDialogHeader, GlassDialogTitle, GlassDialogDescription, GlassDialogFooter } from "@/components/ui/glass-dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { useForm } from "react-hook-form"
import { useAuth } from "@/AuthContext"
import { toast } from "sonner"
import { CircleUserRound } from "lucide-react"

interface EditProfileDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ProfileFormData {
  username: string
  profile_picture: string
}

export default function EditProfileDialog({ open, onOpenChange }: EditProfileDialogProps) {
  const { user, refreshUser } = useAuth()
  const { register, handleSubmit, formState: { errors }, reset } = useForm<ProfileFormData>({
    defaultValues: {
      username: user?.username || "",
      profile_picture: user?.profile_picture || ""
    }
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (user && open) {
      reset({
        username: user.username || "",
        profile_picture: user.profile_picture || ""
      })
    }
  }, [user, open, reset])

  async function onSubmit(data: ProfileFormData) {
    setIsLoading(true)
    try {
      const response = await fetch('/api/auth/update-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        credentials: 'include'
      })
      if (response.ok) {
        const result: { message?: string } = await response.json()
        toast.success(result.message || 'Profile updated successfully')
        await refreshUser()
        onOpenChange(false)
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast.error((errorData as { detail?: string }).detail || 'Failed to update profile')
      }
    } catch (error) {
      toast.error('Failed to update profile: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <GlassDialog open={open} onOpenChange={onOpenChange}>
      <GlassDialogContent>
        <GlassDialogHeader>
          <GlassDialogTitle>Edit Profile</GlassDialogTitle>
          <GlassDialogDescription className="sr-only">
            Update your username and profile picture URL
          </GlassDialogDescription>
        </GlassDialogHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-4 py-4">
            <div className="flex justify-center">
              {user?.profile_picture ? (
                <img src={user.profile_picture} alt="Profile" className="w-24 h-24 rounded-full object-cover" />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                  <CircleUserRound className="w-12 h-12 text-gray-400" />
                </div>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Username"
                {...register("username", {
                  required: "Username is required",
                  minLength: { value: 3, message: "Username must be at least 3 characters" }
                })}
              />
              {errors.username && <p className="text-sm text-red-500">{errors.username.message}</p>}
            </div>
          </div>
          <GlassDialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading} className="cursor-pointer">
              {isLoading ? "Updating..." : "Update Profile"}
            </Button>
          </GlassDialogFooter>
        </form>
      </GlassDialogContent>
    </GlassDialog>
  )
}
