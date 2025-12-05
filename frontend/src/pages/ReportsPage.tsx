/**
 * Reports Page - Campaign Performance Report Generator
 * Agent 18 - Elite Marketers Report Builder
 *
 * Generates professional PDF & Excel reports for:
 * - Client presentations
 * - Stakeholder updates
 * - Board meetings
 * - Investor relations
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  DocumentTextIcon,
  DocumentArrowDownIcon,
  CalendarIcon,
  FunnelIcon,
  ChartBarIcon,
  UsersIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  ClockIcon,
  BriefcaseIcon,
  TrashIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Select } from '@/components/catalyst/select'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Input } from '@/components/catalyst/input'
import { Field, Label } from '@/components/catalyst/fieldset'
import { Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '@/components/catalyst/table'
import { Dialog, DialogActions, DialogBody, DialogDescription, DialogTitle } from '@/components/catalyst/dialog'
import { Divider } from '@/components/catalyst/divider'

import { API_BASE_URL } from '@/config/api'

interface ReportTemplate {
  id: string
  name: string
  description: string
  icon: string
  suitable_for: string[]
}

interface GeneratedReport {
  report_id: string
  report_type: string
  format: string
  start_date: string
  end_date: string
  created_at: string
  status: string
}

// Template icons mapping
const templateIcons: Record<string, any> = {
  'chart-bar': ChartBarIcon,
  'film': SparklesIcon,
  'users': UsersIcon,
  'dollar-sign': CurrencyDollarIcon,
  'calendar': CalendarIcon,
  'briefcase': BriefcaseIcon
}

export default function ReportsPage() {
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [reports, setReports] = useState<GeneratedReport[]>([])
  const [loading, setLoading] = useState(false)
  const [showBuilder, setShowBuilder] = useState(false)

  // Report builder state
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [reportFormat, setReportFormat] = useState<'pdf' | 'excel'>('pdf')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [companyName, setCompanyName] = useState('Your Company')
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadTemplates()
    loadReports()
  }, [])

  const loadTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/templates`)
      const data = await response.json()
      setTemplates(data.templates || [])
    } catch (error) {
      console.error('Error loading templates:', error)
      setTemplates([])
    }
  }

  const loadReports = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/reports?limit=20`)
      const data = await response.json()
      setReports(data.reports || [])
    } catch (error) {
      console.error('Error loading reports:', error)
      setReports([])
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async () => {
    if (!selectedTemplate || !startDate || !endDate) {
      alert('Please fill in all required fields')
      return
    }

    try {
      setGenerating(true)

      const response = await fetch(`${API_BASE_URL}/api/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: selectedTemplate,
          format: reportFormat,
          start_date: startDate,
          end_date: endDate,
          company_name: companyName
        })
      })

      if (!response.ok) {
        throw new Error('Report generation failed')
      }

      const data = await response.json()

      // Download the report immediately
      if (data.report_id) {
        downloadReport(data.report_id)
      }

      // Reset builder and reload reports
      setShowBuilder(false)
      setSelectedTemplate('')
      loadReports()
    } catch (error) {
      console.error('Error generating report:', error)
      alert('Failed to generate report. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const downloadReport = async (reportId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}/download`)

      if (!response.ok) {
        throw new Error('Download failed')
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `report_${reportId}.pdf`

      // Download file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading report:', error)
      alert('Failed to download report')
    }
  }

  const deleteReport = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this report?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Delete failed')
      }

      loadReports()
    } catch (error) {
      console.error('Error deleting report:', error)
      alert('Failed to delete report')
    }
  }

  // Set default date range (last 30 days)
  useEffect(() => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 30)

    setEndDate(end.toISOString().split('T')[0])
    setStartDate(start.toISOString().split('T')[0])
  }, [])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Heading level={1} className="text-white">
                Campaign Reports
              </Heading>
              <Text className="text-zinc-400 mt-1">
                Generate professional reports for clients and stakeholders
              </Text>
            </div>
            <Button color="indigo" onClick={() => setShowBuilder(true)}>
              <DocumentTextIcon className="h-5 w-5" />
              Generate Report
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Report Templates */}
        <div className="mb-12">
          <Heading level={2} className="text-white mb-6">
            Report Templates
          </Heading>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => {
              const IconComponent = templateIcons[template.icon] || DocumentTextIcon
              return (
                <motion.div
                  key={template.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-indigo-500/50 transition-colors cursor-pointer group"
                  onClick={() => {
                    setSelectedTemplate(template.id)
                    setShowBuilder(true)
                  }}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-indigo-500/10 rounded-lg flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
                      <IconComponent className="h-6 w-6 text-indigo-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {template.name}
                      </h3>
                      <p className="text-sm text-zinc-400 mb-3">
                        {template.description}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {template.suitable_for.slice(0, 3).map((tag, idx) => (
                          <Badge key={idx} color="zinc" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>

        <Divider className="my-12" />

        {/* Generated Reports History */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <Heading level={2} className="text-white">
              Report History
            </Heading>
            <Button plain onClick={loadReports}>
              <ArrowPathIcon className="h-5 w-5" />
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
              <Text className="text-zinc-400 mt-4">Loading reports...</Text>
            </div>
          ) : reports.length === 0 ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center">
              <DocumentTextIcon className="h-16 w-16 text-zinc-700 mx-auto mb-4" />
              <Text className="text-zinc-400 mb-4">
                No reports generated yet
              </Text>
              <Button color="indigo" onClick={() => setShowBuilder(true)}>
                Generate Your First Report
              </Button>
            </div>
          ) : (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeader>Report Type</TableHeader>
                    <TableHeader>Format</TableHeader>
                    <TableHeader>Date Range</TableHeader>
                    <TableHeader>Created</TableHeader>
                    <TableHeader>Status</TableHeader>
                    <TableHeader>Actions</TableHeader>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.report_id}>
                      <TableCell className="font-medium text-white">
                        {report.report_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </TableCell>
                      <TableCell>
                        <Badge color={report.format === 'pdf' ? 'red' : 'green'}>
                          {report.format.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-zinc-400">
                        {formatDate(report.start_date)} - {formatDate(report.end_date)}
                      </TableCell>
                      <TableCell className="text-zinc-400">
                        {formatDate(report.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge color="green">Generated</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            plain
                            onClick={() => downloadReport(report.report_id)}
                            title="Download report"
                          >
                            <DocumentArrowDownIcon className="h-5 w-5" />
                          </Button>
                          <Button
                            plain
                            onClick={() => deleteReport(report.report_id)}
                            title="Delete report"
                          >
                            <TrashIcon className="h-5 w-5 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>

      {/* Report Builder Dialog */}
      <Dialog open={showBuilder} onClose={() => setShowBuilder(false)} size="2xl">
        <DialogTitle>Generate Report</DialogTitle>
        <DialogDescription>
          Create a professional campaign performance report for clients and stakeholders.
        </DialogDescription>

        <DialogBody>
          <div className="space-y-6">
            {/* Template Selection */}
            <Field>
              <Label>Report Template</Label>
              <Select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
              >
                <option value="">Select a template...</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </Select>
              {selectedTemplate && (
                <Text className="text-xs text-zinc-500 mt-1">
                  {templates.find(t => t.id === selectedTemplate)?.description}
                </Text>
              )}
            </Field>

            {/* Format Selection */}
            <Field>
              <Label>Report Format</Label>
              <div className="flex gap-4">
                <button
                  onClick={() => setReportFormat('pdf')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    reportFormat === 'pdf'
                      ? 'border-indigo-500 bg-indigo-500/10'
                      : 'border-zinc-700 hover:border-zinc-600'
                  }`}
                >
                  <DocumentTextIcon className="h-8 w-8 mx-auto mb-2 text-red-500" />
                  <div className="text-sm font-medium text-white">PDF</div>
                  <div className="text-xs text-zinc-400 mt-1">Best for presentations</div>
                </button>
                <button
                  onClick={() => setReportFormat('excel')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    reportFormat === 'excel'
                      ? 'border-indigo-500 bg-indigo-500/10'
                      : 'border-zinc-700 hover:border-zinc-600'
                  }`}
                >
                  <ChartBarIcon className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  <div className="text-sm font-medium text-white">Excel</div>
                  <div className="text-xs text-zinc-400 mt-1">Best for data analysis</div>
                </button>
              </div>
            </Field>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-4">
              <Field>
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </Field>
              <Field>
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </Field>
            </div>

            {/* Company Name */}
            <Field>
              <Label>Company Name</Label>
              <Input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter company name for report branding"
              />
            </Field>
          </div>
        </DialogBody>

        <DialogActions>
          <Button plain onClick={() => setShowBuilder(false)}>
            Cancel
          </Button>
          <Button
            color="indigo"
            onClick={generateReport}
            disabled={generating || !selectedTemplate || !startDate || !endDate}
          >
            {generating ? (
              <>
                <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                Generating...
              </>
            ) : (
              <>
                <DocumentTextIcon className="h-5 w-5" />
                Generate Report
              </>
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
