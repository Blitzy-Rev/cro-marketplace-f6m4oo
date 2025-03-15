## WHY - Vision & Purpose

### Purpose & Users

We are solving the problem for our small to mid cap pharma users to use an application that will interface with another engine that predicts chemical and molecular properties for small molecule drug discovery. the idea is that this project will be able to take in a csv format of data in the form of a SMILES coloumn, and a variety of numerical values for many different properties. THe idea is that we will be able to sort through the molecules based on different specifications, different runs and inputs, and be able to upload those molecules in their 'saved library' in a sorted fashion on whatever the user wants, based on types of runs or different organizational libraries that they hold within and organize themselves. The central input to this whole system will still be that csv file that inputs all of SMILES and all associated properties - this platform will organize, sort, distribute molecules, and prepare them for the proper allocation to the proper CRO service. The application additionally wll allow users to select molecules, 'flag' molecules, add them to queue, organize experiments, and submit a query to another segment of the platform which will be the receiving end of the system from the CRO standpoint. The user dashboard will include the computational results, organization of molecules, and all other data organization, and the interface for different services to submit molecules with interactive drag and drop, listing, selection of libraries and molecules, and to submit the molecules for testing. The receiver end will contain all of the data from the user and allow for back and forth communications on price, specifications, final assay strategy, and legal documentation portals. This will allow for a seamless transfer of information, legalities, and compound/ experimental storage for all parties involved. The users on the side of computational data aggregation will be small pharma, and the CROs will be providers of wet lab services. The idea is to seamlessly connect these two processes to optimize efficiency within organizations exponentially. They will use this because it is an all in one suite of tools that outcompetes the rest of the technology out there.  

## WHAT - Core Requirements

### Functional Requirements

**Objective:**  
To develop a **cloud-based application** that allows **small to mid-cap pharma users** to **organize, analyze, and submit small molecules** for **CRO testing** while integrating an **AI engine for molecular property predictions**.

## **1. Core Requirements**

### **1.1 Functional Requirements**

#### **User Management & Authentication**

- **System must** allow users to create and manage accounts with role-based access (Pharma Users, CRO Users, Admins).

- **System must** support secure login using OAuth (Google, ORCID, or corporate SSO).

#### **CSV Upload & Molecular Data Ingestion**

- **Users must be able to** upload a CSV file containing:

  - A **SMILES** column (for molecular structures).

  - Multiple **numerical properties** (logP, MW, IC50, etc.).

- **System must** validate the CSV file format before ingestion.

- **System must** allow users to map CSV headers to system-defined properties.

#### **Molecule Sorting & Organization**

- **Users must be able to**:

  - **Sort molecules** by property (e.g., MW, logP, affinity score).

  - **Filter molecules** based on numerical ranges, flags, and categories.

  - **Group molecules** into custom libraries (e.g., "High Binding Candidates", "Series 1").

- **System must** provide an interactive **drag-and-drop interface** to move molecules between libraries.

#### **Molecule Management & Experiment Queuing**

- **Users must be able to**:

  - **Flag molecules** for priority review.

  - **Add molecules to a queue** for experimental testing.

  - **Batch select molecules** and assign them to specific experimental runs.

- **System must** track molecule status (e.g., "Awaiting Testing", "Submitted to CRO", "Results Available").

#### **Computational Analysis & AI Predictions**

- **System must** interface with an AI engine to:

  - Predict missing molecular properties (e.g., logD, permeability).

  - Rank molecules based on AI-driven screening scores.

  - Provide **heatmaps & plots** for molecular distributions.

#### **CRO Submission & Integration**

- **Users must be able to**:

  - Select a **CRO service** (e.g., **binding assay, ADME profiling**).

  - Submit molecules for testing through an **interactive interface**.

  - Attach **experimental specifications, budget constraints, and legal documents**.

- **CRO Users must be able to**:

  - Receive **molecule submissions with attached metadata**.

  - Communicate **assay pricing, turnaround times, and data requirements**.

  - Upload **assay results** and send them back to pharma users.

#### **Legal & Documentation Portal**

- **System must** support a **secure document exchange** for:

  - NDAs & service agreements.

  - Compliance forms & regulatory approvals.

#### **User Dashboard & Reporting**

- **Users must be able to**:

  - View all molecules in their library.

  - Track **experiment status & CRO communications**.

  - Generate reports on molecule performance & experiment outcomes.

----------

## **2. Technical Requirements**

### **2.1 Tech Stack**

- **Frontend:** React.js (Material UI for UI components).

- **Backend:** FastAPI (Python) or Node.js (Express).

- **Database:** PostgreSQL (Relational) or MongoDB (NoSQL for flexibility).

- **Storage:** AWS S3 (for molecular data storage).

- **AI Model Integration:** PyTorch/TensorFlow-based API for predictions.

### **2.2 System Architecture**

- **Microservices-based** architecture for scalability.

- **RESTful API** for communication between the user interface and AI prediction engine.

- **Real-time messaging** via WebSockets (for CRO-Pharma communication).

----------

## **3. Workflow & User Journey**

1. **Pharma user uploads a CSV** containing molecular data.

2. **System validates and processes molecules**, displaying them in an interactive dashboard.

3. **Users filter, sort, and organize molecules** based on properties and AI predictions.

4. **Users select molecules for testing**, queue them, and submit them to a CRO.

5. **CRO receives molecules**, sets pricing, and uploads results after testing.

6. **Users receive results**, analyze data, and iterate on next experiments.

## 

## **1. System Requirements**

### **1.1 Performance Needs**

- **Batch Processing**: The system must handle CSV files with up to **500,000 molecules** per upload without significant performance degradation.

- **Real-Time Sorting & Filtering**: Users should experience sub-second response times when filtering, searching, or sorting molecular data.

- **Parallel Processing**: AI property predictions should be processed asynchronously to avoid UI blocking.

- **Data Retrieval**: Query times should remain **under 2 seconds** for standard molecule searches.

----------

### **1.2 Security Requirements**

- **Role-Based Access Control (RBAC)**:

  - **Pharma Users** (upload & manage molecular data, submit molecules to CROs).

  - **CRO Users** (view and process submitted molecules, return results).

  - **Admin Users** (manage users, set permissions, review logs).

- **Data Encryption**:

  - **In Transit**: TLS 1.3 for all communications.

  - **At Rest**: AES-256 encryption for all stored data.

- **Audit Logs**: Every user action (e.g., molecule submission, file upload, contract signing) must be logged for regulatory compliance.

- **Secure API Access**: All backend services should require OAuth2-based authentication.

- **Regulatory Compliance**: System must support **21 CFR Part 11** compliance for handling lab-related electronic records.

----------

### **1.3 Scalability Expectations**

- **Database Scaling**: PostgreSQL with partitioning or NoSQL (MongoDB) for flexible querying of large datasets.

- **Horizontal Scaling**: Auto-scaling on AWS Lambda/Fargate to handle increased computational workloads.

- **Storage Expansion**: Molecule data will be stored in **AWS S3 with lifecycle policies** to archive inactive data.

- **Global Deployment**: System should be multi-region to accommodate international CRO collaborations.

----------

### **1.4 Reliability Targets**

- **Uptime SLA**: **99.95% availability** with automated failover.

- **Auto-Recovery**: System should detect and restart failed jobs without manual intervention.

- **Data Backup**: Nightly backups stored in AWS Glacier for long-term retention.

- **Redundant Storage**: High-availability storage with replication across three availability zones.

----------

### **1.5 Integration Constraints**

- **External AI Model**: Seamless API integration with PyTorch/TensorFlow-based molecular prediction engines.

- **LIMS (Laboratory Information Management Systems)**: Ability to integrate with industry-standard LIMS for CRO workflows.

- **E-Signature Services**: Integration with DocuSign for contract management between pharma and CRO users.

- **ERP Systems**: Optional connectivity with pharma R&D financial and procurement systems.

----------

## **2. User Experience (UX) Design**

### **2.1 Key User Flows**

#### **Flow 1: Pharma User Uploads & Organizes Molecules**

**Entry Point**: User logs in and uploads a CSV with molecules.  
**Key Steps**:

1. Drag & drop CSV file.

2. Map file columns to system-defined molecular properties.

3. AI processes molecular properties & auto-fills missing values.

4. User applies filters (e.g., logP \> 3, MW \< 500).

5. User organizes molecules into project libraries.  
   **Success Criteria**: Molecules are uploaded, sorted, and categorized successfully.

**Alternative Flow**:

- If CSV is invalid → User is prompted to correct column mapping.

- If molecules fail AI processing → System logs errors & notifies the user.

----------

#### **Flow 2: Molecule Submission to CRO**

**Entry Point**: User selects molecules from their library for testing.  
**Key Steps**:

1. Clicks **"Submit to CRO"**.

2. Selects a **CRO partner & assay type**.

3. Specifies **testing parameters & budget**.

4. Uploads **required legal documents (e.g., NDAs, contracts)**.

5. CRO receives submission, reviews, and responds with pricing.  
   **Success Criteria**: CRO confirms submission & experiment initiation.

**Alternative Flow**:

- If CRO requires additional specifications → User gets a notification & edits submission.

- If assay pricing is rejected → System allows user to negotiate.

----------

#### **Flow 3: CRO Processes & Returns Experimental Data**

**Entry Point**: CRO logs in to review molecule submission.  
**Key Steps**:

1. Views molecule list & experimental requirements.

2. Uploads assay results in **CSV or structured report format**.

3. Confirms completion & sends invoice (optional integration with billing).

4. Pharma user receives results & updates molecule statuses.  
   **Success Criteria**: Pharma user retrieves experimental data for analysis.

**Alternative Flow**:

- If assay fails → CRO provides failure notes & user can resubmit.

----------

### **2.2 Core Interfaces**

#### **Pharma User Dashboard**

- **Primary Purpose**: Organize & submit molecules.

- **Key Functionality**: CSV upload, molecule sorting, AI predictions, experiment queuing.

- **Critical Components**:

  - Upload Area (CSV drag/drop).

  - Molecule Library View (sortable table, search).

  - Submission Panel (assay selection, CRO details).

- **User Interactions**:

  - Upload molecules & assign properties.

  - Click molecules to select them for testing.

#### **CRO Management Dashboard**

- **Primary Purpose**: Receive & manage molecule submissions.

- **Key Functionality**: Submission review, pricing, results upload.

- **Critical Components**:

  - Submission Queue (sortable list of requests).

  - Assay Pricing/Modification Panel.

  - Data Upload Form (attach reports & CSVs).

- **User Interactions**:

  - View pending molecule submissions.

  - Modify experiment details & communicate with users.

----------

## **3. Business Requirements**

### **3.1 Access & Authentication**

- **User Types**:

  - **Pharma Users** (upload molecules, request CRO services).

  - **CRO Users** (receive requests, return data).

  - **Admin Users** (manage platform-wide settings).

- **Authentication Requirements**:

  - OAuth2-based login (Google, ORCID, SSO).

  - Multi-factor authentication (MFA) for critical actions.

- **Access Control**:

  - **Pharma Users** can only manage their own molecules.

  - **CRO Users** can only access submitted requests.

----------

### **3.2 Business Rules**

- **Data Validation**:

  - SMILES strings must be chemically valid before submission.

  - Numerical values (logP, MW) must be within reasonable ranges.

- **Process Requirements**:

  - Each molecule submission must go through **3 status changes**: Pending, In Progress, Completed.

  - CRO pricing must be reviewed & accepted before experiment execution.

- **Compliance Needs**:

  - Must adhere to **21 CFR Part 11** & **GLP (Good Laboratory Practices)**.

  - All legal documents must be signed via DocuSign before CRO testing.

.