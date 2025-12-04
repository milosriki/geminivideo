import { forwardRef } from 'react'
import clsx from 'clsx'

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  className?: string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  function IconButton({ children, className, ...props }, ref) {
    return (
      <button
        ref={ref}
        type="button"
        className={clsx(
          'inline-flex items-center justify-center rounded-lg p-2',
          'text-zinc-400 hover:text-white hover:bg-zinc-800',
          'transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500',
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)

export default IconButton
