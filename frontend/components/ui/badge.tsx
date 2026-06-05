import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "border-transparent bg-muted text-muted-foreground",
        muted: "border-border bg-muted text-muted-foreground",
        success:
          "border-green-200 bg-green-100 text-green-800 dark:border-green-500/20 dark:bg-green-500/15 dark:text-green-400",
        warning:
          "border-yellow-200 bg-yellow-100 text-yellow-800 dark:border-yellow-500/20 dark:bg-yellow-500/15 dark:text-yellow-400",
        danger:
          "border-red-200 bg-red-100 text-red-800 dark:border-red-500/20 dark:bg-red-500/15 dark:text-red-400",
        info:
          "border-blue-200 bg-blue-100 text-blue-800 dark:border-blue-500/20 dark:bg-blue-500/15 dark:text-blue-400",
        hot:
          "border-orange-200 bg-orange-100 text-orange-700 dark:border-orange-500/20 dark:bg-orange-500/15 dark:text-orange-400",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
