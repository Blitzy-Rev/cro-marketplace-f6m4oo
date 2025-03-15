# CRO Submission Guide

## Introduction

The CRO Submission workflow is a core feature of the Molecular Data Management and CRO Integration Platform, designed to streamline the process of sending molecules for experimental testing at Contract Research Organizations (CROs). This guide provides comprehensive instructions for using the CRO submission features, from selecting molecules and specifying experiments to tracking submissions and receiving results.

The CRO submission process bridges the gap between computational predictions and experimental validation, enabling a seamless transition from in silico analysis to real-world testing. By integrating this workflow directly into the platform, we eliminate the traditional inefficiencies of manual submissions, email-based communications, and disconnected data management.

**Key Benefits:**

- **Streamlined Workflow**: Submit molecules for testing in a few simple steps
- **Integrated Document Management**: Handle legal and compliance documents within the system
- **Real-time Status Tracking**: Monitor the progress of your submissions at every stage
- **Secure Communication**: Communicate directly with CRO partners through the platform
- **Results Integration**: Automatically link experimental results back to your molecules

## CRO Submission Overview

### Key Concepts

| Term | Definition |
| --- | --- |
| Submission | A request to a CRO for experimental testing of selected molecules |
| CRO Service | A specific type of experimental service offered by a CRO partner |
| Experiment Specification | Detailed parameters and requirements for the experimental work |
| Required Documents | Legal and compliance documents necessary for the submission |
| Submission Status | The current stage of the submission in the workflow |

### Workflow Stages

The CRO submission process follows these main stages:

1. **Preparation**: Select molecules, choose a CRO service, and prepare specifications
2. **Documentation**: Complete and sign required legal and compliance documents
3. **Submission**: Submit the request to the CRO for review
4. **Pricing**: Receive and approve pricing and timeline from the CRO
5. **Execution**: CRO performs the experimental work
6. **Results**: CRO uploads results, which are integrated with your molecular data
7. **Review**: Analyze the experimental results and compare with predictions

### User Roles and Responsibilities

**Pharma User Responsibilities:**
- Creating and configuring submissions
- Selecting molecules for testing
- Completing required documents
- Approving pricing and timelines
- Reviewing experimental results

**CRO User Responsibilities:**
- Reviewing incoming submissions
- Providing pricing and timeline estimates
- Performing experimental work
- Uploading results and quality control data
- Communicating about technical details

## Submission Workflow

The CRO submission follows a defined workflow with specific status transitions. Understanding this workflow helps you track your submissions and know what actions are required at each stage.

### Status Definitions

| Status | Description | Next Actions |
| --- | --- | --- |
| DRAFT | Initial creation state, editable by pharma user | Submit to CRO or Cancel |
| SUBMITTED | Sent to CRO but not yet reviewed | Wait for CRO review |
| PENDING_REVIEW | Under review by CRO | Wait for pricing or rejection |
| PRICING_PROVIDED | CRO has provided pricing and timeline | Approve, Reject, or Cancel |
| APPROVED | Pharma has approved pricing and timeline | Wait for experiment to begin |
| IN_PROGRESS | Experimental work in progress at CRO | Wait for results |
| RESULTS_UPLOADED | CRO has uploaded experimental results | Review results |
| RESULTS_REVIEWED | Pharma has reviewed experimental results | Complete submission |
| COMPLETED | Submission workflow completed successfully | No further actions |
| CANCELLED | Submission cancelled by either party | No further actions |
| REJECTED | Submission rejected by CRO or pharma | No further actions |

### Workflow Diagram

The following diagram illustrates the complete submission workflow with status transitions:

```
DRAFT → SUBMITTED → PENDING_REVIEW → PRICING_PROVIDED → APPROVED → IN_PROGRESS → RESULTS_UPLOADED → RESULTS_REVIEWED → COMPLETED
   ↓           ↓            ↓                ↓              ↓             ↓                ↓                  ↓
 CANCELLED   CANCELLED     REJECTED        REJECTED       CANCELLED     CANCELLED        CANCELLED         CANCELLED
```

## Creating a New Submission

To create a new CRO submission, follow these steps:

1. Navigate to the **CRO Submissions** section from the main navigation menu
2. Click the **Create New Submission** button
3. You'll be guided through a multi-step form to configure your submission

### Step 1: Select CRO and Service

1. From the dropdown menu, select a **CRO Partner**
   - The system displays available CROs with active partnerships
   - Each CRO listing includes their specialties and service offerings

2. Select a **Service Type** from the available options
   - Service types vary by CRO but typically include:
     - Binding Assays
     - ADME Studies
     - Solubility Testing
     - Permeability Assays
     - Metabolic Stability
     - Toxicity Screening

3. Enter a **Submission Name** to identify your submission
   - Use a descriptive name that helps you identify the purpose of the submission
   - Example: "Series A Compounds - Binding Assay - September 2023"

4. Provide a detailed **Description** of your submission
   - Include any general information about the purpose of the testing
   - Note any special considerations or priorities

5. Select a **Timeline** preference
   - Standard: Regular processing time (typically 2-3 weeks)
   - Expedited: Faster processing (additional fees may apply)
   - Custom: Specify your required timeline

6. Optionally, enter **Budget Constraints**
   - If you have specific budget limitations, enter them here
   - This helps the CRO provide appropriate pricing options

7. Click **Next** to proceed to molecule selection

## Selecting Molecules for Testing

After configuring the basic submission details, you'll need to select the molecules to be tested by the CRO.

### Selecting from Libraries

1. The molecule selection screen displays your available molecule libraries
2. Select a library from the dropdown or sidebar to view its contents
3. Use the search and filter options to find specific molecules:
   - Text search for molecule IDs or names
   - Property filters for molecular weight, LogP, etc.
   - Status filters to find molecules with specific statuses

4. Select molecules using the checkboxes:
   - Click individual checkboxes to select specific molecules
   - Use the header checkbox to select all molecules on the current page
   - Use Shift+Click to select a range of molecules

5. Selected molecules appear in the "Selected Molecules" section
   - The count updates to show how many molecules are selected
   - You can remove molecules from the selection by clicking the "X" icon

### Adding Molecule Details

For each selected molecule, you can specify additional testing details:

1. Click the **Edit Details** button next to a molecule
2. Specify the **Concentration** for testing
3. Add **Notes** with specific instructions for this molecule
4. Click **Save** to update the molecule details

### Batch Operations

To apply the same settings to multiple molecules:

1. Select the molecules you want to update
2. Click the **Batch Edit** button
3. Enter the concentration and notes to apply to all selected molecules
4. Click **Apply to Selected** to update all molecules

### Adding More Molecules

If you need to add molecules from different libraries:

1. Click the **+ Add More Molecules** button
2. Select another library and find additional molecules
3. Select the molecules to add to your submission
4. Click **Add Selected** to include them in your submission

5. When you've finished selecting molecules, click **Next** to proceed to document management

## Managing Required Documents

Each CRO submission requires specific legal and compliance documents. The system automatically determines which documents are required based on the CRO and service type selected.

### Required Document Types

Depending on your submission, you may need to provide the following documents:

| Document Type | Purpose | Required? | Signature Needed? |
| --- | --- | --- | --- |
| Material Transfer Agreement (MTA) | Legal agreement for transferring materials | Usually | Yes |
| Non-Disclosure Agreement (NDA) | Confidentiality protection | Usually | Yes |
| Experiment Specification Form | Detailed testing parameters | Always | Yes |
| Service Agreement | Terms of service | Sometimes | Yes |
| Safety Data Sheet | Safety information for compounds | If applicable | No |
| Additional Instructions | Supplementary information | Optional | No |

### Document Status

Each document in the system has a status that indicates its current state:

- **Draft**: Document is being prepared
- **Pending Signature**: Document is awaiting signatures
- **Signed**: Document has been signed by all parties
- **Rejected**: Document has been rejected
- **Expired**: Document has expired
- **Archived**: Document has been archived

### Handling Documents

For each required document, you have several options:

1. **Use Existing Document**
   - If you have a previously signed document that's still valid (e.g., an active NDA)
   - Click **Select Existing Document**
   - Choose from the list of available documents
   - The system will verify if the document is valid for this submission

2. **Upload New Document**
   - If you have a prepared document that needs to be signed
   - Click **Upload Document**
   - Select the file from your computer
   - Specify the document type
   - The system will process the document for electronic signature

3. **Fill Online Form**
   - For documents that can be created within the system (e.g., Experiment Specification)
   - Click **Fill Online**
   - Complete the form with required information
   - The system will generate a document for signature

4. **Request Template**
   - If you need a template to prepare a document
   - Click **Request Template**
   - The system will provide a downloadable template
   - Complete the template and upload it when ready

### Electronic Signatures

Many documents require electronic signatures from both pharma and CRO representatives:

1. For documents requiring your signature:
   - Click **Review & Sign**
   - Review the document contents
   - Click **Sign Document**
   - Follow the e-signature process (typically DocuSign integration)
   - The system will track signature status

2. For documents requiring CRO signatures:
   - After you've signed, the CRO will be notified
   - You can track signature status in the document list
   - You'll be notified when all signatures are complete

### Document Verification

Before proceeding to submission, the system verifies that all required documents are properly completed and signed. Any missing or incomplete documents will be flagged, and you'll need to address these issues before submitting.

When all document requirements are satisfied, click **Next** to proceed to the final submission step.

## Specifying Experiment Details

The Experiment Specification form allows you to provide detailed instructions for the CRO regarding how the testing should be performed. This form varies based on the selected service type, but typically includes the following sections:

### General Experiment Information

1. **Experiment Name**: A descriptive name for the experiment
2. **Objective**: The scientific goal of the experiment
3. **Background**: Relevant background information
4. **References**: Any scientific references or previous work

### Assay Parameters

Depending on the service type, you'll need to specify various assay parameters:

**For Binding Assays:**
- Target protein or receptor
- Assay format (radioligand, fluorescence, etc.)
- Concentration range
- Incubation conditions
- Controls to include

**For ADME Studies:**
- Specific ADME parameters to measure
- Test system (cell lines, microsomes, etc.)
- Time points
- Analysis method

**For Solubility Testing:**
- Solubility medium (buffer, simulated fluids, etc.)
- pH conditions
- Temperature
- Time points

### Quality Control Requirements

1. **Replicates**: Number of replicate measurements
2. **Positive Controls**: Required positive control compounds
3. **Negative Controls**: Required negative control compounds
4. **Acceptance Criteria**: Criteria for valid experimental results
5. **Data Analysis**: Specific analysis methods to use

### Reporting Requirements

1. **Data Format**: Preferred format for raw and processed data
2. **Required Calculations**: Specific calculations to include
3. **Visualization**: Required graphs or visualizations
4. **Additional Analyses**: Any specialized analyses

### Special Instructions

Use this section to provide any additional information or special requirements not covered in the standard form fields.

When you've completed the experiment specification, click **Save Specification** to store the information with your submission.

## Submitting the Request

After completing all the required steps, you'll reach the final submission review page:

1. **Review Submission Summary**
   - CRO and service selection
   - Selected molecules (count and list)
   - Document status
   - Experiment specifications

2. **Validation Checks**
   - The system performs final validation to ensure all requirements are met
   - Any issues will be displayed with instructions for resolution

3. **Submission Options**
   - **Save as Draft**: Save your progress without submitting
   - **Submit Request**: Send the submission to the CRO

4. **Confirmation**
   - After clicking Submit, you'll receive a confirmation message
   - The system assigns a unique Submission ID
   - The submission status changes to SUBMITTED
   - The CRO is notified of the new submission

## Tracking Submission Status

Once submitted, you can track the status and progress of your submission:

1. Navigate to the **CRO Submissions** section
2. The submissions list displays all your submissions with their current status
3. Use filters to find specific submissions:
   - Status filter (Draft, Submitted, In Progress, etc.)
   - Date range filter
   - CRO filter
   - Service type filter

4. Click on a submission to view its details page

### Submission Details Page

The submission details page provides comprehensive information about your submission:

1. **Summary Tab**
   - Basic submission information
   - Current status and history
   - Timeline information
   - CRO contact details

2. **Molecules Tab**
   - List of submitted molecules
   - Testing details for each molecule
   - Current status of each molecule

3. **Documents Tab**
   - List of all submission documents
   - Document status and history
   - Options to view, download, or update documents

4. **Specifications Tab**
   - Detailed experiment specifications
   - Any updates or clarifications

5. **Communication Tab**
   - Message history with the CRO
   - Option to send new messages

6. **Results Tab** (appears when results are available)
   - Experimental results data
   - Quality control information
   - Data visualization and analysis tools

### Status Updates

As your submission progresses through the workflow, you'll receive notifications about status changes:

- In-app notifications in the notification center
- Email notifications (if enabled in your preferences)
- Status updates on the dashboard and submission list

## Reviewing and Approving Pricing

After the CRO reviews your submission, they will provide pricing and timeline information:

1. You'll receive a notification when pricing is available
2. Navigate to the submission details page
3. The status will show as PRICING_PROVIDED
4. The Summary tab will display the pricing information:
   - Total cost
   - Currency
   - Estimated turnaround time
   - Any notes or explanations from the CRO

### Approval Process

To approve the pricing and proceed with the submission:

1. Review the pricing and timeline details
2. If acceptable, click the **Approve** button
3. Confirm your approval in the dialog
4. The submission status will update to APPROVED
5. The CRO will be notified of your approval
6. The experimental work will be scheduled

### Requesting Changes

If the pricing or timeline doesn't meet your requirements:

1. Click the **Request Changes** button
2. Enter your concerns or requirements in the dialog
3. Submit your request
4. The CRO will be notified and can provide revised pricing

### Rejecting the Submission

If you decide not to proceed with the submission:

1. Click the **Reject** button
2. Provide a reason for rejection in the dialog
3. Confirm the rejection
4. The submission status will update to REJECTED
5. The CRO will be notified of the rejection

## Communicating with CROs

The platform includes an integrated messaging system for direct communication with CRO partners about your submissions:

### Accessing the Communication Channel

1. Navigate to the submission details page
2. Select the **Communication** tab
3. The message history will be displayed in chronological order

### Sending Messages

1. Type your message in the text field
2. Use the formatting tools for clarity (bold, italic, bullet points, etc.)
3. Use the **@mention** feature to tag specific users
4. Click the attachment icon to include files if needed
5. Click **Send** to deliver your message

### Message Notifications

- You'll receive notifications when the CRO responds to your messages
- The CRO receives notifications when you send messages
- Message counts appear on the Communication tab

### Best Practices for Communication

- Keep messages clear and concise
- Use specific subject lines for new topics
- Reference molecule IDs or experiment details when applicable
- Respond promptly to CRO questions to avoid delays
- Use the appropriate urgency level for your messages

## Receiving and Processing Results

When the CRO completes the experimental work, they will upload the results to the platform:

1. You'll receive a notification when results are available
2. The submission status will update to RESULTS_UPLOADED
3. Navigate to the submission details page
4. Select the **Results** tab to view the experimental data

### Reviewing Results

The Results tab provides tools for reviewing and analyzing the experimental data:

1. **Results Summary**
   - Overview of key findings
   - Quality control metrics
   - Success rate and data completeness

2. **Molecule Results Table**
   - Detailed results for each molecule
   - Comparison with predicted values (if available)
   - Color coding to highlight significant findings

3. **Data Visualization**
   - Interactive charts and graphs
   - Structure-activity relationship views
   - Distribution plots for key parameters

4. **Raw Data Access**
   - Access to raw experimental data
   - Download options for further analysis
   - Links to original result files

### Marking Results as Reviewed

After reviewing the results:

1. Click the **Mark as Reviewed** button
2. Optionally, provide feedback or notes about the results
3. Confirm the action
4. The submission status will update to RESULTS_REVIEWED

### Requesting Additional Information

If you need clarification or additional data:

1. Use the Communication tab to send a message to the CRO
2. Specify what additional information you need
3. The CRO can provide clarification or upload additional data

### Completing the Submission

When you're satisfied with the results and have completed your review:

1. Click the **Complete Submission** button
2. Confirm the action
3. The submission status will update to COMPLETED
4. The results will be permanently linked to the original molecules
5. The molecules' status will update to reflect the completed testing

## Managing Multiple Submissions

If you're working with multiple CRO submissions simultaneously, the platform provides tools to help you manage them efficiently:

### Submission Dashboard

The CRO Submissions dashboard provides an overview of all your submissions:

1. **Status Summary**
   - Count of submissions by status
   - Visual indicators for submissions requiring attention

2. **Recent Activity**
   - Latest status changes and updates
   - Recent communications

3. **Timeline View**
   - Gantt chart of submission timelines
   - Highlighting upcoming deadlines

### Batch Operations

For efficient management of multiple submissions:

1. **Filtering and Sorting**
   - Filter by status, CRO, service type, or date range
   - Sort by various criteria (newest, oldest, priority, etc.)

2. **Batch Actions**
   - Select multiple submissions using checkboxes
   - Apply actions to all selected submissions
   - Available actions depend on submission status

3. **Export Options**
   - Export submission data to CSV or Excel
   - Generate reports for management review
   - Create submission summaries

### Prioritization

To help manage priorities:

1. **Flagging Important Submissions**
   - Mark submissions as high priority
   - Add color coding or tags
   - Set custom reminders

2. **Deadline Tracking**
   - View submissions by due date
   - Receive alerts for approaching deadlines
   - Track time-sensitive submissions

## Troubleshooting Common Issues

### Submission Creation Issues

| Issue | Solution |
| --- | --- |
| Cannot select certain molecules | Verify that the molecules are not already in another active submission |
| Service type not available | Check if the selected CRO offers this service type |
| Cannot proceed past document step | Ensure all required documents are completed and signed |
| Validation errors in experiment specification | Review the highlighted fields and provide the required information |

### Document Management Issues

| Issue | Solution |
| --- | --- |
| Document upload fails | Check file format (PDF preferred) and size (max 10MB) |
| E-signature process stalls | Refresh the page or try a different browser |
| Cannot find existing document | Check document status; expired or archived documents aren't available |
| Document rejected by CRO | Review the rejection reason and update the document accordingly |

### Status Tracking Issues

| Issue | Solution |
| --- | --- |
| Submission stuck in status | Contact the CRO directly or use the communication channel |
| Missing notifications | Check notification settings in your profile |
| Cannot see status updates | Refresh the page or clear browser cache |
| Unexpected status change | Check the submission history for details on the change |

### Results Processing Issues

| Issue | Solution |
| --- | --- |
| Cannot view results | Ensure you have the necessary permissions |
| Results data incomplete | Contact the CRO through the communication channel |
| Download fails | Try a different browser or contact support |
| Visualization not loading | Check your internet connection and browser compatibility |

## CRO User Guide

This section is specifically for CRO users who receive and process submissions from pharmaceutical partners.

### CRO Dashboard

As a CRO user, your dashboard provides an overview of submissions requiring your attention:

1. **New Submissions**: Recently received submissions awaiting review
2. **Active Projects**: Submissions in progress
3. **Pending Results**: Experiments completed but results not yet uploaded
4. **Completed This Month**: Recently completed submissions

### Reviewing New Submissions

When you receive a new submission:

1. Click on the submission in the New Submissions list
2. Review the submission details:
   - Requested service type
   - Molecule information
   - Experiment specifications
   - Required documents

3. Check document completeness and validity
4. Review experiment specifications for feasibility

### Providing Pricing and Timeline

After reviewing the submission:

1. Navigate to the **Pricing and Timeline** section
2. Enter the estimated cost
3. Select the currency
4. Specify the estimated turnaround time in days
5. Provide any notes or explanations
6. Click **Submit Pricing** to send to the pharma partner

### Managing Active Projects

For submissions in progress:

1. Update the status as the work progresses
2. Use the communication channel for questions or updates
3. Document any deviations from the original specifications
4. Track the experiment timeline

### Uploading Results

When the experimental work is complete:

1. Navigate to the submission details page
2. Select the **Results** tab
3. Click **Upload Results**
4. Select the results file (CSV format preferred)
5. Map the results columns to system fields
6. Provide quality control information
7. Add any notes or explanations
8. Click **Submit Results** to complete the upload

### Results Requirements

Results should be uploaded in a structured format:

- CSV file with clear column headers
- Molecule ID column matching the submitted molecules
- Separate columns for each measured parameter
- Units clearly specified
- Quality control data included
- Any deviations or issues noted

## Best Practices

### Planning Your Submissions

1. **Organize Molecules in Advance**
   - Create focused libraries for specific testing purposes
   - Ensure molecules have complete and accurate data
   - Prioritize molecules based on project needs

2. **Understand CRO Capabilities**
   - Review available CRO services before creating submissions
   - Consider specialties and expertise when selecting a CRO
   - Check typical turnaround times for planning purposes

3. **Prepare Documentation Early**
   - Identify required documents before starting a submission
   - Have templates ready for common document types
   - Establish signature workflows with stakeholders

### Efficient Submission Management

1. **Use Descriptive Naming**
   - Create clear, informative submission names
   - Include project, service type, and date in names
   - Use consistent naming conventions across submissions

2. **Batch Similar Requests**
   - Group similar molecules or tests in single submissions
   - Balance batch size with urgency (larger batches may take longer)
   - Consider creating separate submissions for different priorities

3. **Track and Follow Up**
   - Regularly check submission status
   - Respond promptly to CRO questions
   - Set calendar reminders for expected milestones

### Effective Communication

1. **Be Clear and Specific**
   - Provide detailed experiment specifications
   - Reference specific molecules by ID when discussing issues
   - Use precise scientific terminology

2. **Maintain Professional Relationships**
   - Respond promptly to CRO communications
   - Provide constructive feedback
   - Acknowledge good work and successful collaborations

3. **Document Important Decisions**
   - Record key decisions in the communication channel
   - Confirm understanding of complex requirements
   - Summarize verbal discussions in writing

## Related Documentation

For more information on related topics, please refer to these guides:

- **Molecule Management**: Learn how to upload, organize, and manage molecular data
- **Library Organization**: Discover techniques for organizing molecules into libraries
- **Results Analysis**: Explore tools for analyzing and interpreting experimental results

You can access these guides from the Help menu or by searching in the documentation section of the platform.

If you need additional assistance with CRO submissions, please contact our support team through the Help menu.