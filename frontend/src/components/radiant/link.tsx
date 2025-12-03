import * as Headless from '@headlessui/react'
import { Link as RouterLink, type LinkProps as RouterLinkProps } from 'react-router-dom'
import { forwardRef } from 'react'

type LinkProps = Omit<RouterLinkProps, 'to'> & {
  href: string
} & React.ComponentPropsWithoutRef<'a'>

export const Link = forwardRef(function Link(
  { href, ...props }: LinkProps,
  ref: React.ForwardedRef<HTMLAnchorElement>,
) {
  return (
    <Headless.DataInteractive>
      <RouterLink ref={ref} to={href} {...props} />
    </Headless.DataInteractive>
  )
})
