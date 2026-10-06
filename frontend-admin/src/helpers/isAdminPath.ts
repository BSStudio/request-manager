export function isAdminPath(pathname: string) {
  return /^\/admin(\/|$)/.test(pathname);
}
