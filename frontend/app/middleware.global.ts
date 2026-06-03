export default defineNuxtRouteMiddleware((to: any, from: any) => {
  const { isSignedIn } = useAuth()
  
  // Only protect dashboard routes
  if (to.path.startsWith('/dashboard') && !isSignedIn.value) {
    return navigateTo('/')
  }
})
