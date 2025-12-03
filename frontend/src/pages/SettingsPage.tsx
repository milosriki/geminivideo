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
import { Divider } from '@/components/catalyst/divider'
import { Alert, AlertTitle, AlertDescription, AlertActions } from '@/components/catalyst/alert'
import { Gradient } from '@/components/radiant/gradient'
import { Container } from '@/components/salient/Container'
import { TextField, SelectField } from '@/components/salient/Fields'
import { Button as SalientButton } from '@/components/salient/Button'
import { Pricing } from '@/components/salient/Pricing'

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
  const [showRegenerateAlert, setShowRegenerateAlert] = useState(false)

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
                  <Divider soft className="my-4" />
                  <SwitchField>
                    <Label>Push Notifications</Label>
                    <Description>Get browser notifications for job completions.</Description>
                    <Switch checked={pushNotifications} onChange={setPushNotifications} />
                  </SwitchField>
                  <Divider soft className="my-4" />
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
                      <Button outline onClick={() => setShowRegenerateAlert(true)}>Regenerate</Button>
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

              {activeTab === 'billing' && (
                <div className="-m-6">
                  <div className="relative bg-gradient-to-r from-violet-600 to-blue-600 py-8 px-6 rounded-t-xl mb-6">
                    <h3 className="text-xl font-bold text-white">Upgrade Your Plan</h3>
                    <p className="text-violet-100 mt-1">Get unlimited video generation</p>
                    <SalientButton color="white" className="mt-4">Upgrade Now</SalientButton>
                  </div>
                  <Pricing />
                </div>
              )}

              {activeTab === 'appearance' && (
                <div className="text-center py-12">
                  <Text className="text-zinc-400">Coming soon...</Text>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <Alert open={showRegenerateAlert} onClose={() => setShowRegenerateAlert(false)}>
        <AlertTitle>Regenerate API Key</AlertTitle>
        <AlertDescription>
          This will invalidate your current API key. Any applications using it will stop working.
        </AlertDescription>
        <AlertActions>
          <Button plain onClick={() => setShowRegenerateAlert(false)}>Cancel</Button>
          <Button color="amber">Regenerate Key</Button>
        </AlertActions>
      </Alert>
    </div>
  )
}

export default SettingsPage
