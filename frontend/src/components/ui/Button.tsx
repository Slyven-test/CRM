import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function Button({ children, className, ...props }: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium",
        "bg-slate-900 text-white hover:bg-slate-800",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className ?? "",
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}

