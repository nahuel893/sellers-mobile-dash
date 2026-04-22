import type { Variants } from 'framer-motion';

/**
 * Slide variants for seller switching.
 * direction: +1 = next (slides left), -1 = prev (slides right).
 *
 * Spec: RF-SLIDE-TRANSITION-01, RF-SLIDE-TRANSITION-02
 */
export const slideVariants: Variants = {
  enter: (dir: 1 | -1) => ({ x: dir * 40, opacity: 0 }),
  center: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.28, ease: 'easeOut' },
  },
  exit: (dir: 1 | -1) => ({
    x: -dir * 40,
    opacity: 0,
    transition: { duration: 0.22, ease: 'easeIn' },
  }),
};
