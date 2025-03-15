# Library Organization Guide

## Introduction

This guide explains how to organize your molecular data using libraries in the Molecular Data Management and CRO Integration Platform. Libraries provide a powerful way to group, categorize, and manage your molecules for different projects, experiments, or research goals.

## Understanding Libraries

Libraries are collections of molecules that you can organize according to your research needs. They help you manage large sets of molecular data efficiently by grouping related molecules together.

### Library Types

The platform supports different types of libraries to accommodate various organizational needs:

- **Project Libraries**: Group molecules related to specific research projects
- **Compound Class Libraries**: Organize molecules by structural or functional classification
- **Screening Libraries**: Collections of molecules prepared for specific screening campaigns
- **Results Libraries**: Groups of molecules with similar experimental results
- **Custom Libraries**: User-defined collections based on any criteria important to your workflow

### Library Properties

Each library includes the following properties:

- **Name**: Unique identifier for the library
- **Description**: Detailed information about the library's purpose or contents
- **Category**: Optional classification for the library (e.g., Project, Screening, Reference)
- **Visibility**: Public (visible to all users in your organization) or Private (visible only to you)
- **Molecule Count**: The number of molecules currently in the library
- **Created Date**: When the library was created
- **Last Modified**: When the library was last updated

## Creating Libraries

Creating new libraries allows you to organize your molecules into logical groups for easier management and analysis.

### Creating a New Library

To create a new library:

1. Navigate to the **My Libraries** section in the main navigation
2. Click the **+ New Library** button in the upper right corner
3. In the dialog that appears, enter:
   - **Library Name** (required)
   - **Description** (optional)
   - **Category** (optional)
   - **Visibility** setting (Public/Private)
4. Click **Create Library** to save

Your new library will appear in the library list and is ready to have molecules added to it.

### Library Templates

To save time when creating similar libraries, you can use an existing library as a template:

1. In the library list, find the library you want to use as a template
2. Click the **More Options** (⋮) button and select **Create Copy**
3. Modify the name and other properties as needed
4. Choose whether to include molecules from the original library
5. Click **Create Library**

## Managing Libraries

The platform provides several tools for managing your libraries effectively.

### Viewing Libraries

To view your libraries:

1. Click on **My Libraries** in the main navigation
2. The page displays a list of all libraries you have access to
3. You can see key information including name, description, molecule count, and creation date
4. Use the search box to find specific libraries by name or description
5. Use the filter options to narrow down libraries by category, creation date, or other criteria

### Editing Library Properties

To edit a library's properties:

1. In the library list, find the library you want to edit
2. Click the **Edit** (pencil) icon
3. Update the library properties as needed
4. Click **Save Changes**

Note that the library name must remain unique within your account.

### Deleting Libraries

To delete a library:

1. In the library list, find the library you want to delete
2. Click the **Delete** (trash) icon
3. Confirm the deletion in the dialog that appears

**Important**: Deleting a library removes the library organization but does not delete the molecules themselves. Molecules will remain in the system and in any other libraries they belong to.

### Sharing Libraries

To share a library with colleagues:

1. In the library list, find the library you want to share
2. Click the **More Options** (⋮) button and select **Share**
3. In the sharing dialog, you can:
   - Make the library public to your entire organization
   - Share with specific users by entering their email addresses
   - Set permission levels (View Only or Edit)
4. Click **Save Sharing Settings**

Users with View Only access can see the library and its molecules but cannot modify the library or its contents. Users with Edit access can add or remove molecules and modify library properties.

## Working with Molecules in Libraries

Libraries provide powerful tools for organizing and working with your molecular data.

### Adding Molecules to Libraries

There are several ways to add molecules to a library:

**From the Library Detail View:**
1. Open the library by clicking on its name in the library list
2. Click the **Add Molecules** button
3. In the dialog that appears, you can:
   - Search for specific molecules by name, ID, or SMILES
   - Filter molecules by properties
   - Select molecules from the results
4. Click **Add Selected** to add the molecules to the library

**From CSV Upload:**
1. When uploading molecules via CSV, you can specify a target library
2. In the column mapping step, assign molecules to a library
3. All imported molecules will be added to the specified library

**From Molecule Detail View:**
1. When viewing a single molecule, click **Add to Library**
2. Select the target library from the dropdown
3. Click **Add** to add the molecule to the selected library

**From Molecule Search Results:**
1. Perform a search or filtering operation to find molecules
2. Select the molecules you want to add
3. Click **Add to Library** in the action bar
4. Select the target library from the dropdown
5. Click **Add** to add the selected molecules to the library

### Removing Molecules from Libraries

To remove molecules from a library:

1. Open the library by clicking on its name in the library list
2. Select the molecules you want to remove using the checkboxes
3. Click the **Remove from Library** button
4. Confirm the removal in the dialog that appears

**Note**: Removing molecules from a library does not delete the molecules from the system. They will remain available and will still appear in any other libraries they belong to.

### Viewing Library Contents

The library detail view provides two ways to view molecules:

**Table View:**
- Displays molecules in a tabular format with columns for key properties
- Allows sorting by clicking on column headers
- Enables efficient browsing of large molecule sets

**Grid View:**
- Displays molecules as cards with structure visualization
- Provides a more visual representation of your molecular data
- Better for visually comparing molecular structures

Toggle between these views using the view selector buttons in the upper right corner of the library detail page.

### Filtering and Sorting

Libraries support powerful filtering and sorting capabilities:

**Filtering:**
1. In the library detail view, click the **Filter** button
2. In the filter panel, you can filter by:
   - Molecular properties (MW, LogP, etc.) using range sliders
   - Structural features using SMARTS patterns
   - Molecule status (Available, In Testing, etc.)
   - Custom flags or tags
3. Click **Apply Filters** to update the view

**Sorting:**
1. In table view, click on any column header to sort by that property
2. Click again to toggle between ascending and descending order
3. For more complex sorting, use the **Sort By** dropdown to select a property
4. Choose ascending or descending order from the adjacent button

### Batch Operations

Libraries support several batch operations for efficient molecule management:

1. Select multiple molecules using the checkboxes
2. Use the action bar to perform operations such as:
   - **Submit to CRO**: Send selected molecules for experimental testing
   - **Add to Another Library**: Add selected molecules to an additional library
   - **Export**: Download selected molecules as CSV or SDF
   - **Flag/Tag**: Apply custom flags or tags to selected molecules
   - **Change Status**: Update the status of selected molecules

These batch operations help streamline your workflow when working with multiple molecules.

## Library Organization Strategies

Effective library organization can significantly improve your research workflow. Here are some recommended strategies:

### Project-Based Organization

Organize libraries around specific research projects:

- Create a main library for each research project
- Use consistent naming conventions (e.g., "Project-X-Leads")
- Create sub-libraries for different stages (e.g., "Project-X-Hits", "Project-X-Optimized")
- Use the description field to document project goals and progress

### Structural Classification

Organize libraries based on structural features:

- Group molecules with similar scaffolds or pharmacophores
- Create libraries for specific chemical classes
- Use SMARTS patterns in the filtering system to identify structural features
- Leverage the AI prediction capabilities to identify structural similarities

### Workflow-Based Organization

Organize libraries according to your research workflow:

- Create libraries for each stage of your discovery pipeline
- Move molecules between libraries as they progress through stages
- Use status flags to track progress within each library
- Create specialized libraries for molecules ready for CRO submission

### Using Tags and Flags

Enhance library organization with tags and flags:

- Apply consistent tags across libraries for cross-library categorization
- Use flags to highlight molecules of special interest
- Create custom flag categories for your specific workflow needs
- Filter by tags or flags to create dynamic views of your data

## Advanced Features

The platform offers several advanced features for library management:

### Library Comparison

Compare the contents of different libraries:

1. From the library list, select two or more libraries using the checkboxes
2. Click the **Compare** button in the action bar
3. The comparison view shows:
   - Molecules unique to each library
   - Molecules common to all selected libraries
   - Property distribution comparisons

This feature helps identify overlaps and differences between your libraries.

### Library Analytics

Analyze the properties of molecules in your libraries:

1. Open a library and navigate to the **Analytics** tab
2. View visualizations of property distributions:
   - Histograms of molecular weight, LogP, and other properties
   - Scatter plots comparing different properties
   - Structural similarity maps
3. Use these analytics to understand the characteristics of your library and identify trends or outliers

### Automated Library Updates

Set up rules for automatic library updates:

1. From the library detail page, click **Automation Rules**
2. Create rules based on molecule properties or status changes
3. For example:
   - Automatically add molecules with LogP < 5 to a "Drug-Like" library
   - Move molecules with "Failed" test results to a "Deprioritized" library
4. Rules will run automatically when new data is added or existing data is updated

### Library Templates and Sharing

Create standardized library templates for your organization:

1. Administrators can create template libraries with predefined properties and categories
2. Users can create new libraries based on these templates
3. Templates ensure consistent organization across teams and projects
4. Share templates with specific teams or the entire organization

## Best Practices

Follow these best practices for effective library management:

### Naming Conventions

Establish consistent naming conventions for libraries:

- Use prefixes to indicate library type (e.g., "PROJ-" for project libraries)
- Include version or date information for libraries that evolve over time
- Keep names concise but descriptive
- Document naming conventions for your organization

### Documentation

Maintain thorough documentation for your libraries:

- Use the description field to document the library's purpose and contents
- Note any special criteria used for molecule selection
- Document relationships between libraries
- Update descriptions when library contents or purpose changes

### Regular Maintenance

Perform regular library maintenance:

- Review libraries periodically to ensure they remain relevant
- Archive or delete obsolete libraries
- Update library properties and descriptions as projects evolve
- Verify that molecules are correctly categorized

### Collaboration

Optimize libraries for team collaboration:

- Establish clear ownership and permissions for shared libraries
- Use consistent organization schemes across team libraries
- Document library structures in shared team resources
- Consider creating role-specific views for different team members

## Troubleshooting

Solutions for common library management issues:

### Missing Molecules

If molecules appear to be missing from a library:

1. Check if filters are applied that might be hiding the molecules
2. Verify that you have the correct library selected
3. Ensure the molecules were successfully added to the library
4. Check if the molecules were removed by another user (for shared libraries)

### Performance Issues

For libraries with performance issues:

1. Large libraries (>10,000 molecules) may load more slowly
2. Use filters to work with smaller subsets of the library
3. Consider splitting very large libraries into more focused sub-libraries
4. Disable automatic property calculation for faster loading

### Permission Problems

If you encounter permission issues:

1. Verify your access level for the library (View Only vs. Edit)
2. Check if the library owner has changed sharing settings
3. For organization-wide libraries, confirm your role permissions
4. Contact your administrator if you need additional access

### Duplicate Libraries

To manage duplicate libraries:

1. Use the library comparison feature to identify overlaps
2. Consider merging libraries with significant overlap
3. Rename libraries to clarify their unique purpose
4. Archive or delete truly redundant libraries

## Related Topics

Explore these related guides for more information:

- The platform documentation includes information about individual molecule management features
- For details about submitting molecules to CROs for testing, see the CRO Submission guide
- Review the platform help center for additional workflow optimization tips
- Contact support for specific questions about library organization strategies