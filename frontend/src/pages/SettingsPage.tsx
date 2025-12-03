import { useState } from 'react'
import {
  UserIcon,
  CreditCardIcon,
  BellIcon,
  KeyIcon,
  GlobeAltIcon,
  PaintBrushIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Input } from '@/components/catalyst/input'
import { Select } from '@/components/catalyst/select'
import { Switch, SwitchField } from '@/components/catalyst/switch'
import { Fieldset, Field, Label, Description } from '@/components/catalyst/fieldset'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

const tabs = [
  { id: 'profile', name: 'Profile', icon: UserIcon },
  { id: 'billing', name: 'Billing', icon: CreditCardIcon },
  { id: 'notifications', name: 'Notifications', icon: BellIcon },
  { id: 'api', name: 'API Keys', icon: KeyIcon },
  { id: 'integrations', name: 'Integrations', icon: GlobeAltIcon },
  { id: 'appearance', name: 'Appearance', icon: PaintBrushIcon },
]

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [pushNotifications, setPushNotifications] = useState(true)

  return (
    <div className="p-6 lg:p-8">
      <div className="max-w-5xl mx-auto">
        <Heading level={1} className="text-white">Settings</Heading>
        <Text className="text-zinc-400 mt-1">Manage your account and preferences.</Text>

        <div className="flex flex-col lg:flex-row gap-8 mt-8">
          {/* Sidebar */}
          <nav className="w-full lg:w-56 flex-shrink-0">
            <ul className="space-y-1">
              {tabs.map((tab) => (
                <li key={tab.id}>
                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-left transition-colors
                      ${activeTab === tab.id
                        ? 'bg-violet-500/10 text-violet-400'
                        : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                      }
                    `}
                  >
                    <tab.icon className="h-5 w-5" />
                    {tab.name}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
              {activeTab === 'profile' && (
                <Fieldset>
                  <Field>
                    <Label>Full Name</Label>
                    <Input defaultValue="Milos Vukovic" />
                  </Field>
                  <Field>
                    <Label>Email</Label>
                    <Input type="email" defaultValue="milos@ptdfitness.com" />
                  </Field>
                  <Field>
                    <Label>Company</Label>
                    <Input defaultValue="PTD Fitness" />
                  </Field>
                  <Field>
                    <Label>Timezone</Label>
                    <Select defaultValue="Asia/Dubai">
                      <option value="Asia/Dubai">Dubai (GMT+4)</option>
                      <option value="Europe/London">London (GMT+0)</option>
                      <option value="America/New_York">New York (GMT-5)</option>
                    </Select>
                  </Field>
                  <div className="flex justify-end pt-4">
                    <Button color="violet">Save Changes</Button>
                  </div>
                </Fieldset>
              )}

              {activeTab === 'notifications' && (
                <div className="space-y-6">
                  <SwitchField>
                    <Label>Email Notifications</Label>
                    <Description>Receive email updates about your campaigns.</Description>
                    <Switch checked={emailNotifications} onChange={setEmailNotifications} />
                  </SwitchField>
                  <SwitchField>
                    <Label>Push Notifications</Label>
                    <Description>Get browser notifications for job completions.</Description>
                    <Switch checked={pushNotifications} onChange={setPushNotifications} />
                  </SwitchField>
                  <SwitchField>
                    <Label>Weekly Reports</Label>
                    <Description>Receive weekly performance summary emails.</Description>
                    <Switch defaultChecked />
                  </SwitchField>
                </div>
              )}

              {activeTab === 'api' && (
                <div className="space-y-6">
                  <Field>
                    <Label>API Key</Label>
                    <div className="flex gap-2">
                      <Input type="password" defaultValue="sk-xxxxxxxxxxxxxxxx" className="flex-1 font-mono" />
                      <Button outline>Copy</Button>
                      <Button outline>Regenerate</Button>
                    </div>
                    <Description>Use this key to access the GeminiVideo API.</Description>
                  </Field>
                  <Field>
                    <Label>Meta Ads Token</Label>
                    <div className="flex gap-2">
                      <Input type="password" defaultValue="EAAxxxxxxxx" className="flex-1 font-mono" />
                      <Button outline>Update</Button>
                    </div>
                  </Field>
                </div>
              )}

              {activeTab === 'integrations' && (
                <div className="space-y-4">
                  {['Meta Ads', 'TikTok Ads', 'Google Ads', 'YouTube'].map((platform) => (
                    <div key={platform} className="flex items-center justify-between p-4 rounded-lg bg-zinc-800/50">
                      <div>
                        <p className="text-white font-medium">{platform}</p>
                        <p className="text-zinc-400 text-sm">Not connected</p>
                      </div>
                      <Button outline>Connect</Button>
                    </div>
                  ))}
                </div>
              )}

              {(activeTab === 'billing' || activeTab === 'appearance') && (
                <div className="text-center py-12">
                  <Text className="text-zinc-400">Coming soon...</Text>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
