import { clsx } from "clsx";
import type React from "react";

export function IconButton({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={clsx(
        className,
        "flex size-10 items-center justify-center rounded-lg hover:bg-gray-950/5 dark:hover:bg-white/5",
      )}
      {...props}
    >
      {children}
    </button>
  );
}
