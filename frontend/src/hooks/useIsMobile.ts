import { useMediaQuery } from './useMediaQuery';

/**
 * Hook to detect if the current viewport is mobile size
 * @returns boolean - true if viewport is mobile (< 768px)
 */
export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 767px)');
}

/**
 * Hook to detect if the current viewport is tablet size
 * @returns boolean - true if viewport is tablet (768px - 1023px)
 */
export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
}

/**
 * Hook to detect if the current viewport is desktop size
 * @returns boolean - true if viewport is desktop (>= 1024px)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)');
}

/**
 * Hook to detect if the current viewport is small mobile size
 * @returns boolean - true if viewport is very small (< 640px)
 */
export function useIsSmallMobile(): boolean {
  return useMediaQuery('(max-width: 639px)');
}
