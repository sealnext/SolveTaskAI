import * as React from "react"

export interface UseMediaQueryOptions {
  /** When set to `true`, the media query will not be evaluated on the server. Defaults to `false`. */
  ssr?: boolean
  /** The value to return when the media query is not evaluated (e.g., during SSR if `ssr` is `false`). */
  fallback?: boolean
}

/**
 * Custom hook that evaluates a media query and returns whether it matches.
 * 
 * @param query The media query to evaluate
 * @param options Configuration options
 * @returns Boolean indicating whether the media query matches
 */
export function useMediaQuery(
  query: string,
  options: UseMediaQueryOptions = {}
): boolean {
  const { ssr = false, fallback = false } = options

  const [matches, setMatches] = React.useState(() => {
    if (!ssr) return fallback
    
    // Only execute this on the client
    if (typeof window !== "undefined") {
      return window.matchMedia(query).matches
    }
    
    return fallback
  })

  React.useEffect(() => {
    if (typeof window === "undefined") return undefined

    const mediaQueryList = window.matchMedia(query)
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    // Set initial value
    setMatches(mediaQueryList.matches)

    // Use the modern API if available
    mediaQueryList.addEventListener("change", listener)
    
    return () => {
      mediaQueryList.removeEventListener("change", listener)
    }
  }, [query])

  return matches
}
