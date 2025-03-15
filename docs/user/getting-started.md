# Getting Started with the Molecular Data Management and CRO Integration Platform

## Introduction

Welcome to the Molecular Data Management and CRO Integration Platform, a comprehensive solution designed to revolutionize small molecule drug discovery workflows. This platform bridges the gap between computational chemistry and experimental validation by providing a seamless interface for organizing molecular data, predicting properties, and connecting directly with Contract Research Organizations (CROs) for experimental testing.

Key benefits of the platform include:

- **Streamlined Data Management**: Efficiently organize and analyze molecular data from various sources
- **Integrated Workflows**: Connect computational predictions directly with experimental validation
- **Simplified CRO Engagement**: Manage the entire CRO submission process in one system
- **Accelerated Discovery**: Reduce drug discovery cycle times by 30-40%
- **Enhanced Collaboration**: Facilitate seamless communication between research teams and CROs

This guide will help you get started with the platform, covering account setup, navigation, core features, and basic workflows. Whether you're a pharmaceutical researcher, computational chemist, or CRO partner, you'll find the information you need to become productive quickly.

## Getting Started

### Creating Your Account

To access the platform, you need a registered account. Depending on your organization's setup, you may receive an invitation email or need to request access from your administrator.

1. **Via Invitation**: 
   - Click the link in your invitation email
   - Create a password that meets the security requirements
   - Complete your profile information
   - Accept the terms of service

2. **Via Registration**:
   - Navigate to the platform login page
   - Click "Sign Up" to create a new account
   - Enter your email address (use your organizational email)
   - Complete the registration form
   - Verify your email address by clicking the link sent to your inbox

### Logging In

1. Navigate to the platform login page
2. Enter your email address and password
3. Click "Sign In"
4. If your organization uses multi-factor authentication (MFA), you'll be prompted to enter a verification code

**Alternative Login Methods**:
- **Single Sign-On (SSO)**: If your organization has configured SSO, click the "Continue with SSO" button and follow your organization's authentication process
- **ORCID**: Click "Continue with ORCID" to use your scientific ORCID identity

### Password Recovery

If you forget your password:

1. Click "Forgot password?" on the login page
2. Enter your email address
3. Check your email for password reset instructions
4. Create a new password that meets the security requirements

## Platform Overview

### Dashboard

After logging in, you'll land on the dashboard, which provides an overview of your molecular data and recent activity. The dashboard is customized based on your user role:

**For Pharmaceutical Users**:
- **Active Molecules**: Count of molecules in your libraries
- **Libraries**: Number of molecule libraries you have access to
- **Pending Submissions**: CRO submissions awaiting action
- **Recent Results**: Latest experimental results from CROs
- **Recent Activity**: Timeline of recent actions and events
- **Quick Actions**: Shortcuts to common tasks

**For CRO Users**:
- **New Submissions**: Submissions requiring review
- **Active Projects**: Experiments currently in progress
- **Pending Results**: Experiments awaiting result upload
- **Completed This Month**: Recently completed experiments
- **Submission Tables**: Lists of new and in-progress submissions
- **Quick Actions**: Shortcuts to common tasks

### Main Navigation

The platform's main navigation menu is located on the left side of the screen and includes:

- **Dashboard**: Return to the main overview page
- **Upload**: Access the molecule upload interface
- **My Libraries**: View and manage your molecule libraries
- **CRO Submissions**: Create and track submissions to CROs
- **Results**: View and analyze experimental results
- **Settings**: Configure your account and preferences

Depending on your user role and permissions, you may see additional menu items.

### Header Navigation

The top header includes:

- **Search**: Global search functionality for finding molecules, libraries, and submissions
- **Notifications**: Alerts for important events and updates
- **User Menu**: Access to your profile, settings, and logout option
- **Help**: Context-sensitive help and documentation

## Core Workflows

The platform supports four primary workflows that form the backbone of the drug discovery process:

### 1. Molecule Management

The molecule management workflow allows you to import, organize, and analyze molecular structures and their properties:

1. **Upload molecular data** from CSV files containing SMILES structures and properties
2. **Validate and process** the data, ensuring chemical accuracy
3. **View and edit** molecular structures and properties
4. **Search and filter** molecules based on various criteria
5. **Request AI predictions** for additional molecular properties

For detailed instructions, see the [Molecule Management](molecule-management.md) guide.

### 2. Library Organization

The library organization workflow helps you organize molecules into meaningful collections:

1. **Create libraries** to group molecules by project, series, or purpose
2. **Add molecules** to libraries from various sources
3. **Organize libraries** in hierarchical structures
4. **Apply tags and categories** for better organization
5. **Share libraries** with team members for collaboration

For detailed instructions, see the [Library Organization](library-organization.md) guide.

### 3. CRO Submission

The CRO submission workflow streamlines the process of sending molecules for experimental testing:

1. **Select molecules** from your libraries for testing
2. **Choose a CRO and service** from available options
3. **Specify experiment details** and requirements
4. **Manage required documents** for legal and compliance purposes
5. **Track submission status** throughout the process
6. **Communicate with CROs** through the integrated messaging system
7. **Review and approve pricing** provided by the CRO

For detailed instructions, see the [CRO Submission](cro-submission.md) guide.

### 4. Results Analysis

The results analysis workflow helps you interpret and utilize experimental data:

1. **Receive notifications** when results are available
2. **View experimental results** linked to the original molecules
3. **Compare experimental data** with predicted properties
4. **Visualize structure-activity relationships**
5. **Export results** for reporting or further analysis

For detailed instructions, see the [Results Analysis](results-analysis.md) guide.

## Quick Start Guides

### Uploading Your First Molecules

1. Click **Upload** in the main navigation menu
2. Drag and drop your CSV file onto the upload area or click **Browse** to select a file
   - Your CSV must contain at least one column with SMILES strings
   - Additional columns can contain properties like molecular weight, LogP, etc.
3. Once uploaded, you'll be prompted to map CSV columns to system properties
   - The system will automatically detect the SMILES column if possible
   - Map other columns to standard properties or create custom properties
4. Click **Process Molecules** to begin the import
5. After processing completes, you'll see a summary of imported molecules
6. Your molecules are now available in the system and can be organized into libraries

### Creating Your First Library

1. Click **My Libraries** in the main navigation menu
2. Click the **+ New Library** button
3. Enter a name and description for your library
4. Optionally, select a category and add tags
5. Click **Create Library**
6. To add molecules to your library:
   - Navigate to any molecule list (e.g., recent uploads)
   - Select molecules by checking the boxes next to them
   - Click **Add to Library** and select your new library
   - Click **Add**

### Submitting Molecules to a CRO

1. Click **CRO Submissions** in the main navigation menu
2. Click **Create New Submission**
3. Select a CRO partner and service from the dropdown menus
4. Enter a name and description for your submission
5. Click **Next** to proceed to molecule selection
6. Select the molecules you want to test
7. Click **Next** to proceed to document management
8. Upload or complete any required documents
9. Click **Next** to specify experiment details
10. Complete the experiment specification form
11. Review your submission and click **Submit Request**

### Viewing Experimental Results

1. When results are available, you'll receive a notification
2. Click **Results** in the main navigation menu
3. Find your submission in the list and click on it
4. The Results tab displays experimental data linked to your molecules
5. You can view individual results, compare with predictions, and export data

## User Interface Guide

### Common UI Elements

#### Data Tables

Data tables are used throughout the platform to display lists of molecules, libraries, submissions, and results:

- **Sorting**: Click column headers to sort by that column
- **Filtering**: Use the filter button or search box to narrow down results
- **Pagination**: Navigate between pages using the controls at the bottom
- **Selection**: Check boxes to select items for batch operations
- **Actions**: Use the actions menu or buttons to perform operations on selected items

#### Molecule Visualization

Molecule structures are displayed using an interactive viewer:

- **2D/3D Toggle**: Switch between 2D and 3D representations
- **Rotation**: In 3D mode, click and drag to rotate the molecule
- **Zoom**: Use the scroll wheel or pinch gesture to zoom in/out
- **Style**: Change the visualization style using the style selector
- **Export**: Save the current view as an image

#### Forms and Wizards

Multi-step processes use a wizard interface with these common elements:

- **Progress Indicator**: Shows your current step and overall progress
- **Navigation Buttons**: Move between steps using Next/Back buttons
- **Validation**: Required fields are marked with an asterisk (*)
- **Error Messages**: Validation errors appear below the relevant fields
- **Save Draft**: Save your progress to continue later

### Notification System

The platform includes a comprehensive notification system to keep you informed:

- **In-App Notifications**: Appear in the notification center (bell icon)
- **Email Notifications**: Sent for important events (configurable in settings)
- **Toast Notifications**: Temporary pop-ups for immediate feedback
- **Status Updates**: Visual indicators on dashboard and list views

### Search Functionality

The global search allows you to find content across the platform:

1. Click the search icon in the header or press Ctrl+K (Cmd+K on Mac)
2. Enter your search terms
3. Results are categorized by type (molecules, libraries, submissions)
4. Click a result to navigate directly to that item

Advanced search options are available in specific sections of the platform.

## Account Management

### Profile Settings

To update your profile information:

1. Click your user avatar in the top-right corner
2. Select **Profile** from the dropdown menu
3. Update your information as needed:
   - Profile picture
   - Name and contact details
   - Job title and department
   - Time zone and language preferences
4. Click **Save Changes**

### Notification Preferences

To customize which notifications you receive:

1. Click your user avatar in the top-right corner
2. Select **Settings** from the dropdown menu
3. Navigate to the **Notifications** tab
4. Configure your preferences for each notification type:
   - In-app notifications
   - Email notifications
   - Notification frequency
5. Click **Save Preferences**

### Security Settings

To manage your account security:

1. Click your user avatar in the top-right corner
2. Select **Settings** from the dropdown menu
3. Navigate to the **Security** tab
4. From here, you can:
   - Change your password
   - Enable/configure multi-factor authentication
   - View active sessions
   - Review login history

## Getting Help

### In-App Help

The platform includes context-sensitive help throughout the interface:

- **Help Icon**: Click the question mark (?) icon in the top-right corner for help related to your current page
- **Field Tooltips**: Hover over information icons (i) next to fields for specific guidance
- **Guided Tours**: Interactive walkthroughs for key features (available from the Help menu)

### Knowledge Base

The Knowledge Base contains comprehensive documentation on all platform features:

1. Click the Help icon in the top-right corner
2. Select **Knowledge Base** from the dropdown menu
3. Browse articles by category or use the search function
4. Articles include step-by-step instructions, screenshots, and videos

### Support

If you need additional assistance:

1. Click the Help icon in the top-right corner
2. Select **Contact Support** from the dropdown menu
3. Fill out the support request form with:
   - Issue category
   - Detailed description
   - Screenshots (if applicable)
4. Submit the form to create a support ticket
5. You'll receive updates on your ticket via email and in-app notifications

### Troubleshooting Common Issues

| Issue | Solution |
| --- | --- |
| Cannot log in | Check your email and password, ensure caps lock is off, try the password reset function |
| CSV upload fails | Verify your file format, check for special characters in headers, ensure SMILES column is present |
| Molecules not displaying correctly | Verify SMILES strings are valid, try refreshing the browser, check your internet connection |
| Cannot access certain features | Verify your user permissions with your administrator |
| Slow performance | Try refreshing the page, clear browser cache, check your internet connection |

## Next Steps

Now that you're familiar with the basics of the platform, you can explore more detailed documentation on specific features:

- [Molecule Management](molecule-management.md): Learn how to work with molecular data, including upload, visualization, and property management
- [Library Organization](library-organization.md): Discover techniques for organizing molecules into libraries and managing your molecular collections
- [CRO Submission](cro-submission.md): Master the workflow for submitting molecules to CROs for experimental testing
- [Results Analysis](results-analysis.md): Explore tools for analyzing and interpreting experimental results

We recommend starting with the core workflows that align with your immediate needs, then expanding to other areas as you become more comfortable with the platform.

Remember that the platform is designed to be intuitive and user-friendly, with consistent patterns throughout. Don't hesitate to explore and experiment—you can always refer back to the documentation or contact support if you need assistance.

Welcome aboard, and happy discovering!