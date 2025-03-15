# Molecule Management

## Introduction

The Molecular Data Management and CRO Integration Platform revolutionizes small molecule drug discovery workflows by providing powerful tools for organizing, analyzing, and managing molecular data. This guide focuses on the molecule management capabilities, which form the foundation of the platform's functionality.

Effective molecular data organization is critical in modern drug discovery. Without proper tools, researchers often struggle with disconnected spreadsheets, manual data entry, and fragmented information across multiple systems. Our platform addresses these challenges by providing a unified environment where you can:

- Upload and validate molecular structures from CSV files
- Organize molecules into customizable libraries
- Filter and search molecules based on properties and structural features
- Compare molecules to identify trends and patterns
- Seamlessly transition from in silico analysis to experimental validation

By mastering these molecule management features, you'll accelerate your research workflow and make more informed decisions throughout the drug discovery process.

## Platform Overview for Molecule Management

### Key Components

The molecule management interface consists of several key components designed to provide intuitive access to your molecular data:

- **Dashboard**: Your central hub showing molecule statistics, recent uploads, and library information
- **Molecule Viewer**: Interactive 2D/3D visualization of molecular structures with property details
- **Library Browser**: Navigation and management interface for your molecule libraries
- **Property Filters**: Tools for filtering molecules based on properties and structural features
- **Bulk Operations Panel**: Interface for performing actions on multiple molecules simultaneously

These components work together to provide a comprehensive environment for managing your molecular data through every stage of the research process.

### Navigation and Layout

The molecule management interface is organized for efficiency and ease of use:

- **Main Navigation Bar**: Located at the top of the screen, provides access to major platform sections including Dashboard, Upload, My Libraries, CRO Submissions, and Results
- **Sidebar**: Provides contextual navigation within the molecule management section, including library selection and saved filters
- **Toolbar**: Contains action buttons specific to the current view (e.g., upload, filter, export)
- **Content Area**: The main workspace displaying molecules, properties, and visualization tools
- **Notification Center**: Located in the header, shows alerts about processing status, completed uploads, and system messages

To navigate between sections, use the main navigation bar. Within the molecule management section, use the sidebar to access specific libraries or views.

### User Permissions and Roles

Access to molecule management features depends on your assigned role within the platform:

| Role | Upload Capabilities | Library Management | Data Visibility |
| --- | --- | --- | --- |
| Admin | Unlimited uploads | Full control of all libraries | All molecular data |
| Pharma Manager | Unlimited uploads | Create/manage organization libraries | Organization-wide data |
| Pharma Scientist | Standard uploads | Create personal libraries, use shared libraries | Assigned project data |
| CRO Manager | Result uploads only | View submission libraries | Submission-specific data |
| CRO Technician | Result uploads only | View assigned submissions | Assigned submission data |

If you need additional permissions, contact your system administrator or organization manager.

## Uploading Molecular Data

### CSV File Requirements

The platform accepts molecular data in CSV (Comma-Separated Values) format with the following requirements:

- **SMILES Column**: A column containing valid SMILES (Simplified Molecular Input Line Entry System) strings is required
- **Header Row**: The first row must contain column headers
- **File Size**: Maximum 100MB per file
- **Molecule Count**: Up to 500,000 molecules per upload
- **Encoding**: UTF-8 encoding is recommended
- **Additional Columns**: Any number of property columns can be included (e.g., molecular weight, LogP, activity values)

Example of a valid CSV format:

```
SMILES,Compound_ID,Molecular_Weight,LogP,Activity
CC(C)CCO,CPND-001,88.15,1.2,4.5
c1ccccc1,CPND-002,78.11,2.1,3.2
CCN(CC)CC,CPND-003,101.19,0.8,5.1
```

### Upload Process

To upload a CSV file containing molecular data:

1. Navigate to the **Upload** section from the main navigation menu
2. The upload interface will display with a drag-and-drop area
3. Either:
   - Drag and drop your CSV file into the designated area
   - Click the **Browse** button to select a file from your computer
4. Once selected, the system will perform an initial validation check
5. If the file format is valid, you'll proceed to the column mapping step
6. If errors are detected, the system will display specific error messages to help you correct the issues

For large files, a progress bar will display the upload status. You can continue working in other areas of the platform while the upload processes in the background.

### Column Mapping

After uploading a CSV file, you'll need to map the columns to system properties:

1. The column mapping interface will display a preview of your CSV data
2. For each column in your CSV file, select the corresponding system property from the dropdown list
3. The SMILES column must be mapped (this is required)
4. Other common properties include:
   - Compound ID
   - Molecular Weight
   - LogP
   - Melting Point
   - Solubility
   - Activity values (IC50, EC50, etc.)
5. For columns that don't match existing system properties, you can:
   - Select "Custom Property" and provide a name
   - Choose to ignore the column (it won't be imported)
6. Specify units for numerical properties where applicable
7. When finished mapping, click **Next** to proceed

The system will automatically suggest mappings based on column headers, but you should verify these suggestions before proceeding.

### Validation and Error Handling

After column mapping, the system validates your data before final processing:

1. **SMILES Validation**: Each SMILES string is checked for chemical validity
2. **Property Validation**: Numerical properties are checked for appropriate value ranges
3. **Duplicate Detection**: The system identifies potential duplicate molecules

If validation issues are found, you'll see:

1. A validation report summarizing the issues
2. Specific rows with errors highlighted
3. Detailed error messages explaining each issue

Common validation errors include:

- Invalid SMILES syntax
- Non-numerical values in numerical property fields
- Values outside acceptable ranges (e.g., negative molecular weight)
- Duplicate molecules (based on InChI key comparison)

You can choose to:

- **Fix and Re-upload**: Correct the issues in your CSV and upload again
- **Continue with Valid Only**: Proceed with only the valid molecules
- **Skip Validation**: Force import (not recommended for production data)

After successful validation, the system will process the data and add the molecules to your database.

## Viewing and Managing Molecules

### Molecule Dashboard

The Molecule Dashboard provides an overview of your molecular data and recent activity:

1. **Molecule Statistics**: Total molecule count, number of libraries, recent uploads
2. **Recent Activity**: Latest uploads, library changes, and CRO submissions
3. **Quick Actions**: Buttons for common tasks (upload, create library, submit to CRO)
4. **Library Overview**: Summary of your molecule libraries with molecule counts
5. **Status Distribution**: Visualization of molecules by status (available, testing, etc.)

The dashboard is your starting point for molecule management activities and provides at-a-glance information about your data.

### View Options

The platform offers multiple ways to view your molecular data:

1. **Grid View**: Displays molecules as cards with structure visualization and key properties
   - Best for visual comparison of structures
   - Customizable property display
   - Adjustable grid size (small, medium, large)

2. **Table View**: Displays molecules in a tabular format with sortable columns
   - Best for comparing property values
   - Customizable columns
   - Efficient for viewing large datasets
   - Supports in-line editing of certain properties

3. **Structure View**: Focuses on molecular structures with minimal property information
   - Optimized for structural analysis
   - Larger structure visualization
   - Basic property overlay

To switch between views, use the view selector buttons in the toolbar. You can customize each view by clicking the settings icon to choose which properties to display.

### Molecule Details

To view detailed information about a specific molecule:

1. Click on any molecule in grid, table, or structure view
2. The molecule detail page will open, showing:
   - 2D and 3D structure visualization (interactive)
   - All properties, grouped by category
   - Predicted properties with confidence scores
   - Experimental results (if available)
   - History and status information
   - Library memberships
   - Related molecules (based on structural similarity)

The detail view provides comprehensive information about a single molecule and serves as a hub for molecule-specific actions.

### Molecule Status

Molecules in the system have status indicators that reflect their position in the workflow:

| Status | Description | Visual Indicator |
| --- | --- | --- |
| Available | Ready for analysis or submission | Green dot |
| In Queue | Selected for CRO submission but not yet submitted | Yellow clock |
| Submitted | Sent to CRO for testing | Blue arrow |
| Testing | Currently undergoing experimental testing | Orange flask |
| Results Available | Experimental results received | Purple checkbox |
| Failed | Failed validation or testing | Red exclamation |
| Archived | No longer active in current workflow | Gray archive |

Status is automatically updated based on system events (e.g., submission to CRO, results received) but can also be manually changed when needed.

## Filtering and Searching Molecules

### Text Search

To find specific molecules by text attributes:

1. Use the search bar at the top of any molecule list
2. Enter search terms (e.g., molecule ID, name, SMILES fragment)
3. The system searches across multiple fields including:
   - Molecule ID
   - Name
   - SMILES string
   - InChI Key
   - Custom text properties
4. Results update in real-time as you type
5. Advanced search syntax is supported:
   - Quotes for exact phrases: `"benzene ring"`
   - AND/OR operators: `phenol AND "high activity"`
   - Wildcards: `benz*` matches benzene, benzoic, etc.

The search function is case-insensitive and accent-insensitive by default.

### Property Filters

To filter molecules based on property values:

1. Click the **Filter** button in the toolbar
2. The filter panel will open on the right side
3. Select properties to filter by from the available categories:
   - Physical Properties (MW, LogP, etc.)
   - Structural Features
   - Activity Values
   - Custom Properties
4. For numerical properties:
   - Use the sliders to define a range
   - Or enter precise values in the min/max fields
5. For categorical properties:
   - Select one or more values from the dropdown
6. For boolean properties:
   - Toggle the switch on or off
7. Click **Apply Filters** to update the molecule list

Multiple filters can be combined to create complex queries. The molecule count updates in real-time as you adjust filters to show how many molecules match your criteria.

### Status Filters

To filter molecules by status:

1. In the filter panel, expand the "Status" section
2. Select one or more statuses to include:
   - Available
   - In Queue
   - Submitted
   - Testing
   - Results Available
   - Failed
   - Archived
3. Click **Apply Filters** to update the molecule list

Status filters can be combined with property filters and text search for precise molecule selection.

### Saving and Loading Filters

To save filter configurations for future use:

1. Set up your desired filters
2. Click the **Save Filter** button
3. Enter a name for the filter preset
4. Optionally, add a description
5. Choose visibility (personal or shared)
6. Click **Save**

To load a saved filter:

1. Click the **Saved Filters** dropdown
2. Select a filter preset from the list
3. The filter will be applied automatically

Saved filters appear in the sidebar for quick access. You can edit or delete saved filters by clicking the options menu (⋮) next to the filter name.

## Organizing Molecules into Libraries

### Creating Libraries

Libraries help you organize molecules into logical groups for easier management:

1. Navigate to the **My Libraries** section
2. Click the **+ New Library** button
3. In the dialog that appears, enter:
   - **Library Name** (required): A descriptive name for the library
   - **Description** (optional): Details about the library's purpose
   - **Category** (optional): A classification for the library
   - **Visibility**: Choose between Private (only you) or Shared (with team)
4. Click **Create Library**

The new library will appear in your library list and is ready to have molecules added to it.

### Adding Molecules to Libraries

There are several ways to add molecules to libraries:

**From Search or Filter Results:**
1. Search or filter to find the molecules you want to add
2. Select molecules using the checkboxes
3. Click **Add to Library** in the action bar
4. Select the target library from the dropdown
5. Click **Add**

**From Molecule Detail View:**
1. Open a molecule's detail page
2. Click **Add to Library** in the actions menu
3. Select the target library from the dropdown
4. Click **Add**

**During CSV Import:**
1. In the column mapping step of CSV import
2. Select "Add to Library" option
3. Choose the target library
4. All imported molecules will be added to this library

**By Drag and Drop:**
1. In Grid view with the library sidebar open
2. Drag a molecule card to a library in the sidebar
3. Drop to add the molecule to that library

Molecules can belong to multiple libraries simultaneously, allowing flexible organization schemes.

### Removing Molecules from Libraries

To remove molecules from a library:

1. Navigate to the library containing the molecules
2. Select the molecules you want to remove using the checkboxes
3. Click **Remove from Library** in the action bar
4. Confirm the removal when prompted

Removing a molecule from a library does not delete it from the system; it only removes the association with that specific library.

### Library Management

To manage your libraries:

1. Navigate to the **My Libraries** section
2. You'll see a list of all your libraries with:
   - Library name
   - Description
   - Molecule count
   - Creation date
   - Last modified date
   - Visibility status

For each library, you can:

- **Edit**: Change name, description, category, or visibility
- **Share**: Manage access permissions for other users
- **Export**: Download library molecules as CSV or SDF
- **Delete**: Remove the library (molecules are not deleted)
- **Duplicate**: Create a copy of the library with the same molecules

Libraries can be organized hierarchically by creating sub-libraries or using consistent naming conventions.

## Working with Molecular Properties

### Standard Properties

The platform tracks standard molecular properties for all molecules:

| Property | Description | Units | Typical Range |
| --- | --- | --- | --- |
| Molecular Weight | Mass of the molecule | g/mol | 0-1000 |
| LogP | Lipophilicity measure | - | -3 to 7 |
| Hydrogen Bond Donors | Count of H-bond donors | - | 0-10 |
| Hydrogen Bond Acceptors | Count of H-bond acceptors | - | 0-15 |
| Rotatable Bonds | Count of rotatable bonds | - | 0-15 |
| Topological Polar Surface Area | Surface area of polar atoms | Å² | 0-200 |
| Heavy Atom Count | Number of non-hydrogen atoms | - | 0-100 |

These properties are either imported from your CSV files or calculated automatically when missing. You can use these properties for filtering, sorting, and analysis.

### Predicted Properties

The platform can integrate with AI prediction engines to generate predicted properties:

1. Predicted properties are distinguished by a "Predicted" label
2. Each prediction includes a confidence score (0-100%)
3. Predictions are updated automatically when new AI models are available
4. Common predicted properties include:
   - ADME characteristics
   - Toxicity risk
   - Bioavailability
   - Binding affinity

You can compare predicted properties with experimental results to validate the predictions and improve future models.

### Experimental Properties

Experimental properties come from CRO testing results:

1. Experimental properties are distinguished by an "Experimental" label
2. Each value includes metadata about the testing conditions
3. If multiple experiments exist, all values are displayed with dates
4. You can view detailed experimental information by clicking on the property

When both predicted and experimental values exist for the same property, you can easily compare them to evaluate prediction accuracy.

### Custom Properties

You can define custom properties during CSV import or add them manually:

1. To add a custom property to a molecule:
   - Navigate to the molecule detail page
   - Click **Add Property**
   - Enter property name, value, and units
   - Select property type (numeric, text, date, etc.)
   - Click **Save**

2. To add a custom property to multiple molecules:
   - Select molecules in a list view
   - Click **Add Property** in the action bar
   - Configure the property as above
   - Click **Apply to All Selected**

Custom properties can be used in filters, sorting, and visualizations just like standard properties.

## Bulk Operations

### Selecting Multiple Molecules

To work with multiple molecules at once:

1. In any list view (table, grid, or structure), use the checkboxes:
   - Click individual checkboxes to select specific molecules
   - Use the header checkbox to select all molecules on the current page
   - Use Shift+Click to select a range of molecules
   - Hold Ctrl (Cmd on Mac) while clicking to select non-adjacent molecules

2. The selection counter in the action bar shows how many molecules are selected

3. Selection persistence:
   - Selections persist when changing pages within the same view
   - Selections are maintained when changing filters (only matching molecules remain selected)
   - Selections are reset when navigating to a different section

You can save selections for future use by adding the selected molecules to a library.

### Batch Library Assignment

To add multiple molecules to a library at once:

1. Select the molecules you want to add using the checkboxes
2. Click **Add to Library** in the action bar
3. Choose from existing libraries or create a new one
4. Click **Add** to complete the operation

For large selections, the operation runs in the background and you'll receive a notification when complete.

### Batch Property Updates

To update properties for multiple molecules:

1. Select the molecules you want to update
2. Click **Update Properties** in the action bar
3. Choose the property to update
4. Select the update operation:
   - Set Value: Apply the same value to all selected molecules
   - Scale: Multiply existing values by a factor
   - Offset: Add or subtract from existing values
   - Clear: Remove the property value
5. Enter the value to apply
6. Click **Apply** to update all selected molecules

This feature is particularly useful for tagging molecules with experimental batches, assigning priorities, or updating status flags.

### Batch Submission to CRO

To submit multiple molecules to a CRO for testing:

1. Select the molecules you want to submit
2. Click **Submit to CRO** in the action bar
3. You'll be redirected to the CRO submission workflow
4. The selected molecules will be pre-populated in the submission

For detailed instructions on the CRO submission process, refer to the [CRO Submission Guide](cro-submission.md).

## Molecule Comparison

### Selecting Molecules for Comparison

To compare multiple molecules side by side:

1. Select 2-5 molecules using the checkboxes
2. Click **Compare** in the action bar
3. The comparison view will open

Alternatively, from a molecule detail page:
1. Click **Compare With Others**
2. Search for or select molecules to compare with
3. Click **Compare** to open the comparison view

For meaningful comparisons, select molecules with similar structures or properties of interest.

### Comparison View

The comparison view displays molecules side by side with their properties aligned for easy comparison:

1. Molecule structures are displayed at the top of each column
2. Properties are organized in rows across all molecules
3. Property differences are highlighted:
   - Green: Better than average
   - Red: Worse than average
   - Bold: Highest/lowest value in the set
4. You can customize which properties are shown:
   - Click **Customize** to select properties
   - Drag to reorder properties
   - Group related properties together

Controls at the bottom of the view allow you to:
- Add additional molecules to the comparison
- Remove molecules from the comparison
- Export the comparison as an image or PDF
- Save the comparison for future reference

### Property Highlighting

The comparison view uses visual highlighting to emphasize important differences:

1. **Color coding**: 
   - Properties are colored based on desirability (configurable)
   - Green typically indicates favorable values
   - Red typically indicates unfavorable values
   - Intensity varies based on the magnitude of difference

2. **Visual indicators**:
   - Arrows show trends (increasing/decreasing)
   - Stars mark best-in-class values
   - Warning icons highlight concerning values
   - Confidence indicators for predicted properties

3. **Difference calculation**:
   - Absolute and percentage differences are shown
   - Statistical significance is indicated where applicable
   - Reference molecule can be selected for relative comparison

Property highlighting helps you quickly identify similarities and differences between molecules, supporting structure-activity relationship analysis.

## Exporting Molecular Data

### Export Formats

The platform supports several export formats for molecular data:

| Format | File Extension | Best For | Limitations |
| --- | --- | --- | --- |
| CSV | .csv | Spreadsheet analysis, general use | Limited structure information |
| SDF | .sdf | Chemical informatics tools | Large file size |
| SMILES | .smi | Computational chemistry | Limited property support |
| Excel | .xlsx | Spreadsheet analysis with formatting | Maximum 1M molecules |
| JSON | .json | Data integration with other systems | Large file size |

Each format includes molecular structures and property data, with format-specific optimizations.

### Exporting Selected Molecules

To export specific molecules:

1. Select molecules using the checkboxes
2. Click **Export** in the action bar
3. Select the export format
4. Choose which properties to include:
   - All properties
   - Only visible properties (based on current view)
   - Custom selection
5. Configure export options:
   - Include header row (CSV)
   - Compression (for large exports)
   - Structure representation (2D, 3D, both)
6. Click **Export** to generate and download the file

For large selections, the export processes in the background and provides a download link when complete.

### Exporting Libraries

To export an entire library:

1. Navigate to the **My Libraries** section
2. Find the library you want to export
3. Click the options menu (⋮) and select **Export**
4. Configure the export as described above
5. Click **Export** to generate and download the file

Library exports include all molecules in the library with their properties and library metadata.

### Exporting Search Results

To export the results of a search or filter operation:

1. Perform your search or apply filters
2. Click **Export** in the toolbar
3. Configure the export as described above
4. Choose whether to export:
   - All matching molecules
   - Only the current page
   - A specified maximum number
5. Click **Export** to generate and download the file

Search result exports include the search criteria in the metadata to document what was exported.

## Best Practices

### Organizing Molecules Effectively

Follow these recommendations for effective molecule organization:

1. **Create purpose-driven libraries**:
   - Organize by project, target, or chemical series
   - Create separate libraries for different research stages
   - Use consistent naming conventions

2. **Implement hierarchical organization**:
   - Start with broad categories (e.g., "Project X")
   - Create sub-libraries for specific aspects (e.g., "Project X - Leads")
   - Use tags for cross-cutting classifications

3. **Leverage status flags**:
   - Update molecule status to reflect workflow position
   - Use status filters to focus on relevant molecules
   - Automate status updates where possible

4. **Regular library maintenance**:
   - Review and update libraries periodically
   - Archive completed or inactive libraries
   - Merge similar libraries when appropriate

These practices ensure your molecular data remains organized and accessible as your research evolves.

### Naming Conventions

Consistent naming conventions improve clarity and searchability:

1. **Library naming**:
   - Include project identifier: "PROJ001-LeadCompounds"
   - Indicate purpose: "PROJ001-Screening-April2023"
   - Use version numbers for iterations: "PROJ001-Leads-v2"

2. **Molecule identifiers**:
   - Use consistent prefixes: "COMP-", "MOL-", "CHEM-"
   - Include series information: "SER-A-001"
   - Maintain consistent numbering schemes
   - Document naming schemes for team reference

3. **Custom properties**:
   - Use clear, descriptive names: "Solubility_pH7_4"
   - Include units in property names when not standard
   - Be consistent with capitalization and separators

4. **Saved filters and views**:
   - Include purpose in name: "HighSolubility_LowToxicity"
   - Add date for time-sensitive filters: "QCReview_May2023"

Well-designed naming conventions improve collaboration and reduce confusion, especially in large teams.

### Performance Considerations

For optimal performance when working with large datasets:

1. **CSV import optimization**:
   - Split very large files (>100K molecules) into smaller batches
   - Remove unnecessary columns before import
   - Ensure clean data to minimize validation errors
   - Schedule large imports during off-peak hours

2. **Efficient filtering**:
   - Apply more selective filters first to reduce the dataset
   - Use indexed properties for faster filtering
   - Save complex filter combinations for reuse
   - Consider creating focused libraries instead of repeatedly filtering

3. **View optimization**:
   - Use table view for very large datasets
   - Limit visible columns to those needed
   - Increase page size only when necessary
   - Disable auto-calculation of properties for faster loading

4. **Export considerations**:
   - Export only necessary properties
   - Use CSV for faster exports of large datasets
   - Consider incremental exports of very large libraries
   - Schedule large exports during off-peak hours

Following these guidelines ensures the platform remains responsive even with large molecular datasets.

### Collaboration Workflows

Effective team collaboration on molecule management:

1. **Shared libraries**:
   - Create team libraries with appropriate permissions
   - Establish clear ownership and maintenance responsibilities
   - Document the purpose and scope of shared libraries
   - Use consistent organization across team libraries

2. **Communication practices**:
   - Add descriptive notes to libraries and molecules
   - Document significant changes or decisions
   - Use standardized flags and tags for status indication
   - Leverage the notification system for important updates

3. **Role-based workflows**:
   - Define clear responsibilities for different team roles
   - Create role-specific views and dashboards
   - Establish handoff procedures between workflow stages
   - Document approval processes for key transitions

4. **Versioning approach**:
   - Create snapshot libraries at important milestones
   - Document version history in library descriptions
   - Use date-stamped libraries for periodic reviews
   - Maintain an audit trail of significant changes

These practices promote efficient teamwork while maintaining data integrity and traceability.

## Troubleshooting

### CSV Import Issues

Solutions for common CSV import problems:

| Issue | Possible Causes | Solutions |
| --- | --- | --- |
| "Invalid file format" | Wrong file type, corrupted file | Ensure file is properly formatted CSV; try re-saving from spreadsheet software |
| "SMILES column required" | Missing SMILES column mapping | Map a column to the SMILES property; verify SMILES strings are valid |
| "Invalid SMILES strings" | Incorrect chemical notation | Check SMILES syntax; use a chemical structure validator before import |
| "Duplicate molecules detected" | Same structure appears multiple times | Use the deduplication option; decide how to handle duplicates |
| "Import timeout" | File too large, server busy | Split into smaller files; try during off-peak hours |

For persistent import issues:
1. Check your CSV file encoding (UTF-8 recommended)
2. Remove any special characters from headers
3. Ensure no empty rows or columns
4. Verify property values are in appropriate ranges
5. Contact support with error messages and a sample file

### Search and Filter Problems

Troubleshooting for search and filter functionality:

| Issue | Possible Causes | Solutions |
| --- | --- | --- |
| No search results | Too restrictive criteria, typos | Broaden search terms; check spelling; use wildcards |
| Too many results | Search terms too general | Add more specific terms; use property filters to narrow results |
| Filtering not working | Invalid property ranges, data issues | Check min/max values; verify property data exists |
| Slow search performance | Complex query, large dataset | Simplify search criteria; narrow scope with pre-filtering |
| Inconsistent results | Mixed data formats, unit mismatches | Standardize property formats and units |

To optimize search and filter operations:
1. Start with broader searches and progressively narrow
2. Use indexed properties for faster filtering
3. Create focused libraries for frequently used subsets
4. Save complex filters for reuse
5. Check for unit consistency in numerical properties

### Library Management Issues

Solutions for common library management problems:

| Issue | Possible Causes | Solutions |
| --- | --- | --- |
| Cannot create library | Permission issues, name conflict | Verify permissions; choose a unique library name |
| Missing molecules | Filters applied, removal by another user | Check for active filters; verify library membership |
| Cannot add to library | Permission issues, molecule already present | Check library permissions; look for duplicate entries |
| Library not appearing | Visibility settings, deleted library | Check library sharing settings; verify library exists |
| Slow library loading | Too many molecules, complex properties | Optimize view settings; consider splitting large libraries |

For effective library management:
1. Regularly review and maintain libraries
2. Document library purposes and organization scheme
3. Archive inactive libraries rather than deleting
4. Use consistent naming and organization across libraries
5. Set appropriate permissions for shared libraries

### Performance Issues

Troubleshooting for performance problems with large datasets:

| Issue | Possible Causes | Solutions |
| --- | --- | --- |
| Slow page loading | Too many molecules, complex view | Reduce page size; simplify view; apply filters |
| Unresponsive interface | Resource-intensive operations | Cancel running operations; refresh browser; clear cache |
| Export timeout | Too many molecules, all properties included | Reduce export size; select fewer properties; use CSV format |
| Visualization lag | Complex molecular structures, 3D rendering | Switch to 2D view; reduce the number of visible molecules |
| Filter operation slow | Non-indexed properties, complex criteria | Use indexed properties; simplify filter criteria |

To improve overall performance:
1. Use table view for large datasets
2. Limit visible properties to those needed
3. Create focused libraries instead of filtering large sets
4. Schedule resource-intensive operations during off-peak hours
5. Close unused browser tabs and applications

## Related Documentation

For more information on related topics, please refer to these guides:

- [Library Organization Guide](library-organization.md): Detailed instructions for creating and managing molecule libraries, including advanced organization strategies and best practices.

- [CRO Submission Guide](cro-submission.md): Comprehensive information about submitting molecules to Contract Research Organizations for experimental testing, tracking submissions, and processing results.

- Results Analysis: Tools and techniques for analyzing experimental results, comparing with predictions, and making data-driven decisions.

- AI Predictions: Understanding how the platform generates property predictions, interpreting confidence scores, and using predictions in your workflow.

- Data Visualization: Advanced visualization capabilities for exploring molecular data, identifying trends, and communicating findings.

For additional assistance, please contact the platform support team through the Help menu or support@moleculeflow.com.