import { clsx } from "clsx";
import type React from "react";
import { useEffect, useRef } from "react";

// Play icon component
function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  return h > 0
    ? `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
    : `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function Video({ className, ...props }: React.ComponentProps<"video">) {
  const videoContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const videoContainer = videoContainerRef.current;
    if (!videoContainer) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          videoContainer.setAttribute("data-offscreen", "");
        } else {
          videoContainer.removeAttribute("data-offscreen");
        }
      },
      { threshold: 0.5 },
    );

    observer.observe(videoContainer);

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div
      ref={videoContainerRef}
      className={clsx(
        className,
        "group aspect-video w-full rounded-2xl bg-gray-950 dark:bg-gray-900",
      )}
    >
      <video
        {...props}
        poster={props.poster || undefined}
        preload="metadata"
        controls
        onPlay={(e) => e.currentTarget.setAttribute("data-playing", "")}
        onPause={(e) => {
          if (!videoContainerRef.current?.hasAttribute("data-offscreen")) {
            e.currentTarget.removeAttribute("data-playing");
          }
        }}
        className={clsx(
          "aspect-video w-full rounded-2xl",
          "sm:data-[offscreen]:data-[playing]:fixed sm:data-[offscreen]:data-[playing]:right-4 sm:data-[offscreen]:data-[playing]:bottom-4 sm:data-[offscreen]:data-[playing]:z-10 sm:data-[offscreen]:data-[playing]:max-w-md sm:data-[offscreen]:data-[playing]:rounded-xl sm:data-[offscreen]:data-[playing]:shadow-lg",
        )}
      />
    </div>
  );
}

export function TimestampButton({
  start,
  videoId,
  className,
}: {
  start: number;
  videoId: string;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => {
        const video = document.getElementById(videoId) as HTMLVideoElement;
        if (video) {
          video.currentTime = start;
          video.play();
        }
      }}
      className={clsx(
        className,
        "inline-flex items-center gap-1 rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600 hover:bg-blue-500/20 dark:bg-blue-400/10 dark:text-blue-400 dark:hover:bg-blue-400/20",
      )}
    >
      <PlayIcon className="size-3" />
      {formatTime(start)}
    </button>
  );
}
