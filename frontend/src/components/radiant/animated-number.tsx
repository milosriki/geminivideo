import { useSpring, useTransform, motion, useInView } from 'framer-motion'
import { useEffect, useRef } from 'react'
import { clsx } from 'clsx'

export function AnimatedNumber({
    value,
    duration = 2,
    decimals = 0,
    className,
}: {
    value: number
    duration?: number
    decimals?: number
    className?: string
}) {
    const ref = useRef(null)
    const inView = useInView(ref, { once: true, margin: '-100px' })

    // Using a spring that feels responsive but smooth
    const spring = useSpring(0, {
        mass: 0.8,
        stiffness: 75,
        damping: 15
    })

    const display = useTransform(spring, (current) =>
        current.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        })
    )

    useEffect(() => {
        if (inView) {
            spring.set(value)
        }
    }, [inView, value, spring])

    return (
        <motion.span ref={ref} className={clsx('tabular-nums', className)}>
            {display}
        </motion.span>
    )
}
