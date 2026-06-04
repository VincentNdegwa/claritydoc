<template>
  <SidebarProvider>
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg">
              <div class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <FileText class="size-4" />
              </div>
              <div class="grid flex-1 text-left text-sm leading-tight">
                <div class="truncate font-semibold">ClarityDoc</div>
                <div class="truncate text-xs">Document Intelligence</div>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Platform</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton as-child :is-active="isActive('/dashboard')">
                  <NuxtLink to="/dashboard">
                    <FileText />
                    <div>Dashboard</div>
                  </NuxtLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton as-child :is-active="isActive('/dashboard/documents')">
                  <NuxtLink to="/dashboard/documents">
                    <FileText />
                    <div>Document Vault</div>
                  </NuxtLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton as-child :is-active="isActive('/dashboard/commitments')">
                  <NuxtLink to="/dashboard/commitments">
                    <Calendar />
                    <div>Commitments</div>
                  </NuxtLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton as-child :is-active="isActive('/dashboard/billing')">
                  <NuxtLink to="/dashboard/billing">
                    <CreditCard />
                    <div>Telemetry & Billing</div>
                  </NuxtLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <SidebarMenuButton size="lg">
                  <Avatar class="size-8 rounded-lg">
                    <AvatarImage v-if="user?.imageUrl" :src="user.imageUrl" :alt="user?.fullName || 'User'" />
                    <AvatarFallback class="rounded-lg">
                      {{ user?.firstName?.[0] || user?.emailAddress?.[0] || 'U' }}
                    </AvatarFallback>
                  </Avatar>
                  <div class="grid flex-1 text-left text-sm leading-tight">
                    <div class="truncate font-semibold">{{ user?.fullName || 'User' }}</div>
                    <div class="truncate text-xs">{{ user?.emailAddresses?.[0]?.emailAddress }}</div>
                  </div>
                  <ChevronsUpDown class="ml-auto size-4" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                class="w-[--reka-popper-anchor-width] min-w-56 rounded-lg"
                side="bottom"
                align="end"
                :side-offset="4"
              >
                <DropdownMenuLabel class="p-0 font-normal">
                  <div class="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                    <Avatar class="size-8 rounded-lg">
                      <AvatarImage v-if="user?.imageUrl" :src="user.imageUrl" :alt="user?.fullName || 'User'" />
                      <AvatarFallback class="rounded-lg">
                        {{ user?.firstName?.[0] || user?.emailAddress?.[0] || 'U' }}
                      </AvatarFallback>
                    </Avatar>
                    <div class="grid flex-1 text-left text-sm leading-tight">
                      <div class="truncate font-semibold">{{ user?.fullName || 'User' }}</div>
                      <div class="truncate text-xs">{{ user?.emailAddress }}</div>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                  <DropdownMenuItem>
                    <User />
                    Account
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <CreditCard />
                    Billing
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings />
                    Settings
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="signOut">
                  <LogOut />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
    
    <SidebarInset>
      <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger />
        <Separator orientation="vertical" class="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink as-child>
                <NuxtLink to="/dashboard">Dashboard</NuxtLink>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <template v-for="(item, index) in breadcrumbs" :key="index">
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink v-if="item.href" as-child>
                  <NuxtLink :to="item.href">{{ item.label }}</NuxtLink>
                </BreadcrumbLink>
                <BreadcrumbPage v-else>{{ item.label }}</BreadcrumbPage>
              </BreadcrumbItem>
            </template>
          </BreadcrumbList>
        </Breadcrumb>
      </header>
      
      <main class="flex-1 overflow-auto p-4">
        <slot />
      </main>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import { FileText, ChevronsUpDown, User, CreditCard, Settings, LogOut, Calendar } from '@lucide/vue'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarRail, SidebarTrigger } from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'

interface BreadcrumbItem {
  label: string
  href?: string
}

const route = useRoute()
const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const metaBreadcrumbs = route.meta.breadcrumbs
  if (typeof metaBreadcrumbs === 'function') {
    return metaBreadcrumbs(route) as BreadcrumbItem[]
  }
  return (metaBreadcrumbs as BreadcrumbItem[]) || []
})

const { user } = useUser()
const { signOut } = useAuth()

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>
