"""
PDF Builder - Professional PDF Report Generation
Agent 18 - Investment-Grade PDF Reports using ReportLab

Creates beautiful, branded PDF reports suitable for:
- C-suite executives
- Board presentations
- Client deliverables
- Investor updates
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from datetime import datetime
from typing import Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)


class PDFBuilder:
    """
    Professional PDF report builder
    Creates investor-grade reports with charts, tables, and insights
    """

    def __init__(self, output_path: str):
        """Initialize PDF builder with output path"""
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional appearance"""

        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=20,
            spaceBefore=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Metric style (for large numbers)
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor('#2c5aa0'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Metric label style
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6a6a6a'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        # Insight box style
        self.styles.add(ParagraphStyle(
            name='InsightText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2a2a2a'),
            spaceAfter=10,
            spaceBefore=10,
            leftIndent=20,
            rightIndent=20
        ))

    def build_report(self, report_content: Dict[str, Any]) -> str:
        """
        Build complete PDF report from content

        Args:
            report_content: Report data from ReportGenerator

        Returns:
            Path to generated PDF file
        """
        logger.info(f"Building PDF report: {report_content['report_id']}")

        # Create PDF document
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        # Build story (content flow)
        story = []

        # Cover page
        story.extend(self._build_cover_page(report_content))

        # Executive summary
        story.append(PageBreak())
        story.extend(self._build_executive_summary(report_content))

        # Key metrics overview
        story.append(PageBreak())
        story.extend(self._build_metrics_overview(report_content))

        # Detailed data sections
        story.extend(self._build_data_sections(report_content))

        # Insights and recommendations
        story.append(PageBreak())
        story.extend(self._build_insights_section(report_content))
        story.extend(self._build_recommendations_section(report_content))

        # Build PDF
        doc.build(story)

        logger.info(f"PDF report generated: {self.output_path}")
        return self.output_path

    def _build_cover_page(self, content: Dict[str, Any]) -> List:
        """Build professional cover page"""
        elements = []

        # Add company logo if provided
        if content.get('company_logo') and os.path.exists(content['company_logo']):
            try:
                logo = Image(content['company_logo'], width=2*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.5*inch))
            except Exception:
                logger.warning("Could not load company logo")

        # Add spacer to center content
        elements.append(Spacer(1, 2*inch))

        # Report title
        title = Paragraph(
            f"{content['report_type'].replace('_', ' ').title()} Report",
            self.styles['CustomTitle']
        )
        elements.append(title)

        # Date range
        date_range = content.get('date_range', {})
        date_text = f"{date_range.get('start', '')} to {date_range.get('end', '')}"
        date_para = Paragraph(date_text, self.styles['Normal'])
        date_para.alignment = TA_CENTER
        elements.append(date_para)
        elements.append(Spacer(1, 0.5*inch))

        # Company name
        company_para = Paragraph(
            f"<b>{content.get('company_name', 'Your Company')}</b>",
            self.styles['Normal']
        )
        company_para.alignment = TA_CENTER
        elements.append(company_para)

        # Generated date
        generated_date = datetime.fromisoformat(content['generated_at'].replace('Z', '+00:00'))
        generated_text = f"Generated: {generated_date.strftime('%B %d, %Y')}"
        gen_para = Paragraph(generated_text, self.styles['Normal'])
        gen_para.alignment = TA_CENTER
        elements.append(gen_para)

        return elements

    def _build_executive_summary(self, content: Dict[str, Any]) -> List:
        """Build executive summary section"""
        elements = []

        # Section title
        elements.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))

        # Summary text
        summary_text = content.get('summary', 'No summary available.')
        # Convert markdown-style bold to ReportLab bold
        summary_text = summary_text.replace('**', '<b>').replace('**', '</b>')

        summary_para = Paragraph(summary_text, self.styles['BodyText'])
        elements.append(summary_para)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_metrics_overview(self, content: Dict[str, Any]) -> List:
        """Build key metrics overview with large numbers"""
        elements = []

        elements.append(Paragraph("Key Metrics", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))

        # Get overall metrics
        data = content.get('data', {})
        overall = data.get('overall_metrics', {})

        if overall:
            # Create metrics grid
            metrics = [
                ('Total Spend', f"${overall.get('total_spend', 0):,.0f}"),
                ('Total Revenue', f"${overall.get('total_revenue', 0):,.0f}"),
                ('ROAS', f"{overall.get('overall_roas', 0):.2f}x"),
                ('Conversions', f"{overall.get('total_conversions', 0):,}"),
                ('CTR', f"{overall.get('overall_ctr', 0)*100:.2f}%"),
                ('CPA', f"${overall.get('overall_cpa', 0):.2f}")
            ]

            # Create 2x3 grid of metrics
            metric_data = []
            for i in range(0, len(metrics), 2):
                row_elements = []
                for j in range(2):
                    if i + j < len(metrics):
                        label, value = metrics[i + j]
                        cell_content = [
                            Paragraph(value, self.styles['Metric']),
                            Paragraph(label, self.styles['MetricLabel'])
                        ]
                        row_elements.append(cell_content)
                metric_data.append(row_elements)

            # Flatten for table
            table_data = []
            for row in metric_data:
                table_row = []
                for cell in row:
                    # Create nested table for each metric
                    inner_table = Table([[p] for p in cell], colWidths=[2.5*inch])
                    inner_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    table_row.append(inner_table)
                table_data.append(table_row)

            metrics_table = Table(table_data, colWidths=[3.25*inch, 3.25*inch])
            metrics_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))

            elements.append(metrics_table)
            elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_data_sections(self, content: Dict[str, Any]) -> List:
        """Build detailed data sections"""
        elements = []

        data = content.get('data', {})

        # Campaign performance table
        if 'campaigns' in data:
            elements.append(PageBreak())
            elements.append(Paragraph("Campaign Details", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 0.2*inch))

            campaigns = data['campaigns']
            if campaigns:
                # Table headers
                table_data = [
                    ['Campaign', 'Impressions', 'Clicks', 'Conv.', 'CTR', 'ROAS', 'Spend']
                ]

                # Add campaign rows
                for camp in campaigns[:10]:  # Limit to top 10
                    table_data.append([
                        Paragraph(camp.get('name', 'N/A')[:30], self.styles['Normal']),
                        f"{camp.get('total_impressions', 0):,}",
                        f"{camp.get('total_clicks', 0):,}",
                        f"{camp.get('total_conversions', 0):,}",
                        f"{camp.get('ctr', 0)*100:.2f}%",
                        f"{camp.get('avg_roas', 0):.2f}x",
                        f"${camp.get('total_spend', 0):,.0f}"
                    ])

                campaign_table = Table(table_data, colWidths=[1.8*inch, 0.9*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.8*inch])
                campaign_table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                    # Data rows
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),

                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),

                    # Padding
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))

                elements.append(campaign_table)
                elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_insights_section(self, content: Dict[str, Any]) -> List:
        """Build insights section with highlighted boxes"""
        elements = []

        insights = content.get('insights', [])

        if insights:
            elements.append(Paragraph("Key Insights", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 0.2*inch))

            for insight in insights:
                # Create colored box based on insight type
                bg_color = {
                    'positive': colors.HexColor('#e8f5e9'),
                    'negative': colors.HexColor('#ffebee'),
                    'info': colors.HexColor('#e3f2fd'),
                    'warning': colors.HexColor('#fff3e0')
                }.get(insight.get('type', 'info'), colors.HexColor('#f5f5f5'))

                # Insight title
                title_text = f"<b>{insight.get('title', 'Insight')}</b>"
                title_para = Paragraph(title_text, self.styles['Normal'])

                # Insight description
                desc_para = Paragraph(insight.get('description', ''), self.styles['InsightText'])

                # Create table for colored background
                insight_table = Table(
                    [[title_para], [desc_para]],
                    colWidths=[6.5*inch]
                )
                insight_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))

                elements.append(insight_table)
                elements.append(Spacer(1, 0.15*inch))

        return elements

    def _build_recommendations_section(self, content: Dict[str, Any]) -> List:
        """Build recommendations section"""
        elements = []

        recommendations = content.get('recommendations', [])

        if recommendations:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("Recommendations", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 0.2*inch))

            # Create recommendations table
            table_data = [
                ['Priority', 'Recommendation', 'Impact', 'Effort']
            ]

            for rec in recommendations:
                # Priority badge
                priority = rec.get('priority', 'medium').upper()
                priority_color = {
                    'HIGH': colors.HexColor('#d32f2f'),
                    'MEDIUM': colors.HexColor('#f57c00'),
                    'LOW': colors.HexColor('#388e3c')
                }.get(priority, colors.grey)

                priority_para = Paragraph(
                    f"<font color='white'><b>{priority}</b></font>",
                    self.styles['Normal']
                )

                # Recommendation text
                rec_text = f"<b>{rec.get('title', '')}</b><br/>{rec.get('description', '')}"
                rec_para = Paragraph(rec_text, self.styles['Normal'])

                table_data.append([
                    priority_para,
                    rec_para,
                    rec.get('impact', 'N/A'),
                    rec.get('effort', 'N/A')
                ])

            rec_table = Table(table_data, colWidths=[0.8*inch, 3.5*inch, 1.3*inch, 0.9*inch])
            rec_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Priority column background
                ('BACKGROUND', (0, 1), (0, -1), priority_color),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),

                # Data rows
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),

                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))

            elements.append(rec_table)

        return elements


def generate_pdf_report(report_content: Dict[str, Any], output_path: str) -> str:
    """
    Generate PDF report from content

    Args:
        report_content: Report data from ReportGenerator
        output_path: Path to save PDF file

    Returns:
        Path to generated PDF
    """
    builder = PDFBuilder(output_path)
    return builder.build_report(report_content)
