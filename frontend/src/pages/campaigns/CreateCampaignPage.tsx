import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  SparklesIcon,
  PhotoIcon,
  PlayIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Input } from '@/components/catalyst/input'
import { Select } from '@/components/catalyst/select'
import { Fieldset, Field, Label, Description } from '@/components/catalyst/fieldset'
import { Checkbox, CheckboxField, CheckboxGroup } from '@/components/catalyst/checkbox'
import { Radio, RadioField, RadioGroup } from '@/components/catalyst/radio'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Badge } from '@/components/catalyst/badge'
import { useCampaignStore } from '@/stores'

// Step Indicator Component
function WizardProgress({ currentStep, steps }: { currentStep: number; steps: string[] }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => {
        const stepNum = index + 1
        const isCompleted = stepNum < currentStep
        const isCurrent = stepNum === currentStep

        return (
          <div key={step} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all
                  ${isCompleted ? 'bg-violet-600 text-white' : ''}
                  ${isCurrent ? 'bg-violet-600 text-white ring-4 ring-violet-600/30' : ''}
                  ${!isCompleted && !isCurrent ? 'bg-zinc-800 text-zinc-400' : ''}
                `}
              >
                {isCompleted ? <CheckIcon className="h-5 w-5" /> : stepNum}
              </div>
              <span className={`text-xs mt-2 ${isCurrent ? 'text-white' : 'text-zinc-500'}`}>
                {step}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`w-20 h-0.5 mx-2 ${
                  stepNum < currentStep ? 'bg-violet-600' : 'bg-zinc-800'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// Step 1: Campaign Setup
function SetupStep() {
  const { wizard, updateWizard } = useCampaignStore()

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6"
    >
      <div>
        <Heading level={2} className="text-white">Campaign Setup</Heading>
        <Text className="text-zinc-400 mt-1">Define your campaign basics and targeting.</Text>
      </div>

      <Fieldset>
        <Field>
          <Label>Campaign Name</Label>
          <Input
            value={wizard.name}
            onChange={(e) => updateWizard({ name: e.target.value })}
            placeholder="e.g., PTD Summer Transformation"
          />
        </Field>

        <Field>
          <Label>Objective</Label>
          <Select
            value={wizard.objective}
            onChange={(e) => updateWizard({ objective: e.target.value })}
          >
            <option value="">Select objective...</option>
            <option value="conversions">Conversions - Drive leads & sales</option>
            <option value="traffic">Traffic - Send visitors to your site</option>
            <option value="awareness">Awareness - Reach new audiences</option>
          </Select>
        </Field>

        <Field>
          <Label>Daily Budget (AED)</Label>
          <Input
            type="number"
            value={wizard.budget}
            onChange={(e) => updateWizard({ budget: Number(e.target.value) })}
            placeholder="1000"
          />
          <Description>Recommended: AED 500-2000 for testing</Description>
        </Field>

        <Field>
          <Label>Platforms</Label>
          <CheckboxGroup>
            {['Meta (Facebook/Instagram)', 'TikTok', 'YouTube', 'Google Ads'].map((platform) => (
              <CheckboxField key={platform}>
                <Checkbox
                  checked={wizard.platforms.includes(platform)}
                  onChange={(checked) => {
                    if (checked) {
                      updateWizard({ platforms: [...wizard.platforms, platform] })
                    } else {
                      updateWizard({ platforms: wizard.platforms.filter((p) => p !== platform) })
                    }
                  }}
                />
                <Label>{platform}</Label>
              </CheckboxField>
            ))}
          </CheckboxGroup>
        </Field>

        <Field>
          <Label>Target Audience</Label>
          <Select
            value={wizard.targetAudience}
            onChange={(e) => updateWizard({ targetAudience: e.target.value })}
          >
            <option value="">Select audience...</option>
            <option value="executives">Executives 40+ in Dubai</option>
            <option value="professionals">Professionals 30-50</option>
            <option value="women">Women seeking transformation</option>
            <option value="men">Men seeking transformation</option>
            <option value="custom">Custom Audience</option>
          </Select>
        </Field>
      </Fieldset>
    </motion.div>
  )
}

// Step 2: Creative Setup
function CreativeStep() {
  const { wizard, updateWizard } = useCampaignStore()

  const styleOptions = [
    { id: 'ugc', name: 'UGC Style', description: 'Authentic, phone-filmed look', icon: '📱' },
    { id: 'professional', name: 'Professional', description: 'Studio quality production', icon: '🎬' },
    { id: 'mixed', name: 'Mixed', description: 'Best of both worlds', icon: '✨' },
  ]

  const hookStyles = [
    { id: 'problem', name: 'Problem-Solution', example: '"Tired of..." → "Here\'s how..."' },
    { id: 'transformation', name: 'Transformation', example: 'Before/After story arc' },
    { id: 'social-proof', name: 'Social Proof', example: '"1000+ clients transformed..."' },
    { id: 'curiosity', name: 'Curiosity Hook', example: '"The secret Dubai trainers use..."' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6"
    >
      <div>
        <Heading level={2} className="text-white">AI Creative Setup</Heading>
        <Text className="text-zinc-400 mt-1">Configure how AI generates your video ads.</Text>
      </div>

      {/* Upload Zone */}
      <div className="border-2 border-dashed border-zinc-700 rounded-xl p-8 text-center hover:border-violet-500/50 transition-colors cursor-pointer">
        <PhotoIcon className="h-12 w-12 text-zinc-500 mx-auto" />
        <p className="text-white mt-4 font-medium">Upload source videos</p>
        <p className="text-zinc-400 text-sm mt-1">Drag & drop or click to browse</p>
        <p className="text-zinc-500 text-xs mt-2">MP4, MOV up to 500MB</p>
      </div>

      {/* Creative Style */}
      <Field>
        <Label>Creative Style</Label>
        <div className="grid grid-cols-3 gap-4 mt-2">
          {styleOptions.map((style) => (
            <button
              key={style.id}
              onClick={() => updateWizard({ creativeStyle: style.id })}
              className={`
                p-4 rounded-xl border text-left transition-all
                ${wizard.creativeStyle === style.id
                  ? 'border-violet-500 bg-violet-500/10'
                  : 'border-zinc-800 hover:border-zinc-700'
                }
              `}
            >
              <span className="text-2xl">{style.icon}</span>
              <p className="text-white font-medium mt-2">{style.name}</p>
              <p className="text-zinc-400 text-sm">{style.description}</p>
            </button>
          ))}
        </div>
      </Field>

      {/* Hook Style */}
      <Field>
        <Label>Hook Style</Label>
        <RadioGroup
          value={wizard.hookStyle}
          onChange={(value) => updateWizard({ hookStyle: value })}
        >
          <div className="grid grid-cols-2 gap-4 mt-2">
            {hookStyles.map((hook) => (
              <RadioField key={hook.id}>
                <Radio value={hook.id} />
                <div className="ml-3">
                  <Label>{hook.name}</Label>
                  <Description>{hook.example}</Description>
                </div>
              </RadioField>
            ))}
          </div>
        </RadioGroup>
      </Field>

      {/* Number of Variants */}
      <Field>
        <Label>Number of Variants</Label>
        <div className="flex items-center gap-4 mt-2">
          {[1, 3, 5, 10].map((num) => (
            <button
              key={num}
              onClick={() => updateWizard({ variants: num })}
              className={`
                px-6 py-3 rounded-lg font-medium transition-all
                ${wizard.variants === num
                  ? 'bg-violet-600 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }
              `}
            >
              {num}
            </button>
          ))}
        </div>
        <Description>More variants = better testing opportunities</Description>
      </Field>
    </motion.div>
  )
}

// Step 3: Review & Launch
function ReviewStep() {
  const { wizard } = useCampaignStore()

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6"
    >
      <div>
        <Heading level={2} className="text-white">Review & Launch</Heading>
        <Text className="text-zinc-400 mt-1">Review your campaign settings before launching.</Text>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
          <p className="text-zinc-400 text-sm">Campaign Name</p>
          <p className="text-white font-medium mt-1">{wizard.name || 'Unnamed Campaign'}</p>
        </div>
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
          <p className="text-zinc-400 text-sm">Daily Budget</p>
          <p className="text-white font-medium mt-1">AED {wizard.budget.toLocaleString()}</p>
        </div>
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
          <p className="text-zinc-400 text-sm">Platforms</p>
          <div className="flex flex-wrap gap-2 mt-1">
            {wizard.platforms.map((p) => (
              <Badge key={p} color="violet">{p.split(' ')[0]}</Badge>
            ))}
          </div>
        </div>
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
          <p className="text-zinc-400 text-sm">Variants</p>
          <p className="text-white font-medium mt-1">{wizard.variants} videos to generate</p>
        </div>
      </div>

      {/* Preview Section */}
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-white font-medium">Generated Previews</p>
          <Badge color="yellow">Pending Generation</Badge>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: Math.min(wizard.variants, 3) }).map((_, i) => (
            <div
              key={i}
              className="aspect-[9/16] rounded-lg bg-zinc-800 flex items-center justify-center"
            >
              <div className="text-center">
                <PlayIcon className="h-8 w-8 text-zinc-600 mx-auto" />
                <p className="text-zinc-500 text-xs mt-2">Variant {i + 1}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Launch Options */}
      <div className="rounded-xl bg-gradient-to-r from-violet-900/50 to-fuchsia-900/50 border border-violet-500/30 p-6">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-6 w-6 text-violet-400" />
          <div>
            <p className="text-white font-medium">Ready to Launch</p>
            <p className="text-zinc-300 text-sm">
              AI will generate {wizard.variants} video variants and publish to selected platforms.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Main Wizard Component
export function CreateCampaignPage() {
  const navigate = useNavigate()
  const { wizard, nextStep, prevStep, resetWizard } = useCampaignStore()
  const steps = ['Setup', 'Creative', 'Review']

  const handleNext = () => {
    if (wizard.step < 3) {
      nextStep()
    } else {
      // Launch campaign
      console.log('Launching campaign:', wizard)
      // TODO: API call to create campaign
      resetWizard()
      navigate('/campaigns')
    }
  }

  const handleBack = () => {
    if (wizard.step > 1) {
      prevStep()
    } else {
      navigate('/')
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <WizardProgress currentStep={wizard.step} steps={steps} />

      <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 p-8">
        <AnimatePresence mode="wait">
          {wizard.step === 1 && <SetupStep key="setup" />}
          {wizard.step === 2 && <CreativeStep key="creative" />}
          {wizard.step === 3 && <ReviewStep key="review" />}
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-zinc-800">
          <Button plain onClick={handleBack} className="gap-2">
            <ArrowLeftIcon className="h-4 w-4" />
            {wizard.step === 1 ? 'Cancel' : 'Back'}
          </Button>
          <Button color="violet" onClick={handleNext} className="gap-2">
            {wizard.step === 3 ? (
              <>
                <SparklesIcon className="h-4 w-4" />
                Launch Campaign
              </>
            ) : (
              <>
                Next
                <ArrowRightIcon className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default CreateCampaignPage
