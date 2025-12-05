import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  HomeIcon,
  FilmIcon,
  FolderIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  SparklesIcon,
  PlusCircleIcon,
  QuestionMarkCircleIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline'
import { SidebarLayout } from '@/components/catalyst/sidebar-layout'
import { Sidebar, SidebarBody, SidebarHeader, SidebarItem, SidebarLabel, SidebarSection, SidebarFooter } from '@/components/catalyst/sidebar'
import { Navbar, NavbarItem, NavbarSection, NavbarSpacer } from '@/components/catalyst/navbar'
import { Avatar } from '@/components/catalyst/avatar'
import { Dropdown, DropdownButton, DropdownMenu, DropdownItem, DropdownLabel, DropdownDivider } from '@/components/catalyst/dropdown'
import { DemoModeIndicator } from '@/components/DemoModeIndicator'

const navigation = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Create', href: '/create', icon: PlusCircleIcon },
  { name: 'Projects', href: '/projects', icon: FolderIcon },
  { name: 'Assets', href: '/assets', icon: FilmIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Ad Spy', href: '/spy', icon: MagnifyingGlassIcon },
  { name: 'AI Studio', href: '/studio', icon: SparklesIcon },
]

const secondaryNavigation = [
  { name: 'Resources', href: '/resources', icon: BookOpenIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  { name: 'Help & Docs', href: '/help', icon: QuestionMarkCircleIcon },
]

export function DashboardLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <SidebarLayout
      sidebar={
        <Sidebar>
          <SidebarHeader>
            <SidebarItem href="/" className="mb-2">
              <SparklesIcon className="h-6 w-6 text-violet-500" />
              <SidebarLabel className="text-lg font-bold bg-gradient-to-r from-violet-500 to-fuchsia-500 bg-clip-text text-transparent">
                GeminiVideo
              </SidebarLabel>
            </SidebarItem>
          </SidebarHeader>

          <SidebarBody>
            <SidebarSection>
              {navigation.map((item) => (
                <SidebarItem
                  key={item.name}
                  href={item.href}
                  current={location.pathname === item.href}
                >
                  <item.icon className="h-5 w-5" />
                  <SidebarLabel>{item.name}</SidebarLabel>
                </SidebarItem>
              ))}
            </SidebarSection>

            <SidebarSection className="mt-auto">
              {secondaryNavigation.map((item) => (
                <SidebarItem
                  key={item.name}
                  href={item.href}
                  current={location.pathname === item.href}
                >
                  <item.icon className="h-5 w-5" />
                  <SidebarLabel>{item.name}</SidebarLabel>
                </SidebarItem>
              ))}
            </SidebarSection>
          </SidebarBody>

          <SidebarFooter>
            <Dropdown>
              <DropdownButton as={SidebarItem}>
                <Avatar
                  src="/avatar.jpg"
                  initials="MV"
                  className="bg-violet-500 text-white"
                />
                <SidebarLabel>Milos Vukovic</SidebarLabel>
              </DropdownButton>
              <DropdownMenu anchor="top start" className="min-w-64">
                <DropdownItem href="/settings">
                  <Cog6ToothIcon className="h-4 w-4" />
                  <DropdownLabel>Settings</DropdownLabel>
                </DropdownItem>
                <DropdownDivider />
                <DropdownItem href="/logout">
                  <DropdownLabel>Sign out</DropdownLabel>
                </DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </SidebarFooter>
        </Sidebar>
      }
      navbar={
        <Navbar>
          <NavbarSpacer />
          <NavbarSection>
            <NavbarItem href="/create" className="gap-2">
              <PlusCircleIcon className="h-5 w-5" />
              New Campaign
            </NavbarItem>
          </NavbarSection>
        </Navbar>
      }
    >
      <Outlet />
      <DemoModeIndicator position="bottom-right" showControls={true} />
    </SidebarLayout>
  )
}

export default DashboardLayout
