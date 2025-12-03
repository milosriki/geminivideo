<<<<<<< HEAD
import * as Headless from '@headlessui/react'
import { Link as RouterLink } from 'react-router-dom'
=======
/**
 * TODO: Update this component to use your client-side framework's link
 * component. We've provided examples of how to do this for Next.js, Remix, and
 * Inertia.js in the Catalyst documentation:
 *
 * https://catalyst.tailwindui.com/docs#client-side-router-integration
 */

import * as Headless from '@headlessui/react'
>>>>>>> 6f56b443fc530e149eac70a51a1753661922ccf6
import React, { forwardRef } from 'react'

export const Link = forwardRef(function Link(
  props: { href: string } & React.ComponentPropsWithoutRef<'a'>,
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  return (
    <Headless.DataInteractive>
<<<<<<< HEAD
      <RouterLink to={props.href} {...props} ref={ref} />
=======
      <a {...props} ref={ref} />
>>>>>>> 6f56b443fc530e149eac70a51a1753661922ccf6
    </Headless.DataInteractive>
  )
})
