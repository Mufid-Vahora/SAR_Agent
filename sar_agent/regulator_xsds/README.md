# XSD Format Templates for SAR Agent

This directory contains two different XSD (XML Schema Definition) formats that can be used by the LLM to generate compliant XML reports from pipe-formatted data.

## Overview

The system provides two distinct XSD formats to handle different levels of data complexity:

1. **Format 1: Complex Comprehensive Format** (`format1_complex.xsd`)
2. **Format 2: Simple Flat Format** (`format2_simple.xsd`)

## Architecture Integration

The XSD formats are fully integrated into the SAR Agent microservices architecture:

- **Port 8082**: Template Fetcher - Downloads and indexes XSD schemas
- **Port 8083**: RAG Service - Provides semantic search over XSD schemas  
- **Port 8084**: LLM Filler - Generates XML using LLM with RAG context
- **Port 8085**: Validator - Validates XML against XSD schemas
- **Port 8086**: Format Selector - Analyzes data and recommends XSD format
- **Port 8087**: Orchestrator - Coordinates the complete pipeline

## Format Selection

The system automatically analyzes pipe-formatted data and selects the appropriate XSD format based on complexity metrics. You can also manually specify which format to use.

### Automatic Selection

The `Format Selector` service analyzes your data and recommends the best format:

```bash
# Analyze pipe data
curl -X POST "http://localhost:8086/analyze" \
  -H "Content-Type: application/json" \
  -d '{"pipe_data": "EntityName|Test Corp|Type:Company"}'
```

### Manual Selection

You can explicitly choose a format by telling the LLM:
- "Use Format 1 (Complex)" for comprehensive reporting
- "Use Format 2 (Simple)" for basic reporting

## Format 1: Complex Comprehensive Format

**File:** `format1_complex.xsd`  
**Namespace:** `http://www.regulator.gov/complex`  
**Root Element:** `ComplexReport`

### Characteristics
- **Structure:** Nested with complex types
- **Complexity:** High
- **Flexibility:** High
- **Validation:** Comprehensive
- **Relationships:** Complex entity relationships
- **Entities:** Multiple entities supported
- **Transactions:** Detailed transaction tracking

### Best For
- Complex financial crime investigations
- Multi-entity relationships
- Detailed risk assessments
- Comprehensive compliance reporting
- Regulatory submissions requiring full context
- Cases with multiple transactions and entities

### Data Requirements
- Multiple entities with relationships
- Complex transaction patterns
- Detailed risk indicators
- Supporting documentation
- Beneficial ownership information
- Geographic coordinates
- Intermediary details

### Example Use Cases
- Money laundering investigations
- Terrorist financing cases
- Complex fraud schemes
- Multi-jurisdictional cases
- High-value transaction monitoring

## Format 2: Simple Flat Format

**File:** `format2_simple.xsd`  
**Namespace:** `http://www.regulator.gov/simple`  
**Root Element:** `SimpleReport`

### Characteristics
- **Structure:** Flat with simple types
- **Complexity:** Low
- **Flexibility:** Medium
- **Validation:** Basic
- **Relationships:** Simple relationships
- **Entities:** Single entity focus
- **Transactions:** Basic transaction info

### Best For
- Basic suspicious activity reports
- Simple transaction monitoring
- Quick compliance alerts
- Standard regulatory filings
- Cases with limited complexity
- Routine monitoring reports

### Data Requirements
- Single primary entity
- Basic transaction information
- Standard risk assessment
- Essential contact details
- Basic location information

### Example Use Cases
- Standard SAR filings
- Basic transaction alerts
- Simple compliance reports
- Routine monitoring
- Quick risk assessments

## Pipe-Formatted Data Structure

The system accepts pipe-formatted data with the following structure:

```
FieldName|Value|AdditionalInfo|Metadata
```

### Example Data
```
EntityName|TechCorp Solutions LLC|Type:Company|Structure:LLC
TransactionID|TXN-001|Type:Wire|Status:Completed|Amount:50000.00
RiskLevel|High|Score:8.5|Threshold:7.0|Escalation:Required
```

### Complex Data Example
```
# Multiple entities with relationships
EntityName|TechCorp Solutions LLC|Type:Company|Structure:LLC
RelatedEntity1|TechCorp Holdings Inc|Type:Parent Company|Relationship:100% Ownership
RelatedEntity2|TechCorp International Ltd|Type:Subsidiary|Relationship:Majority Control

# Multiple transactions
TransactionID1|TXN-001|Type:Wire|Status:Completed|Amount:50000.00
TransactionID2|TXN-002|Type:ACH|Status:Suspicious|Amount:75000.00

# Detailed risk assessment
RiskFactors|Unusual Transaction Pattern|Severity:High|Confidence:85%|Source:AI Analysis
RiskFactors|Multiple High-Value Transfers|Severity:Medium|Confidence:90%|Source:Pattern Recognition
```

## API Usage

### 1. Complete Pipeline (Recommended)

Use the orchestrator service for end-to-end processing:

```bash
curl -X POST "http://localhost:8087/pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "pipe_data": "EntityName|Test Corp|Type:Company",
    "validate_output": true,
    "use_rag": true
  }'
```

### 2. Individual Services

#### Format Selection
```bash
curl -X POST "http://localhost:8086/analyze" \
  -H "Content-Type: application/json" \
  -d '{"pipe_data": "EntityName|Test Corp|Type:Company"}'
```

#### XML Generation
```bash
curl -X POST "http://localhost:8084/fill_with_pipe_data" \
  -H "Content-Type: application/json" \
  -d '{
    "pipe_data": "EntityName|Test Corp|Type:Company",
    "use_rag": true
  }'
```

#### XML Validation
```bash
curl -X POST "http://localhost:8085/validate_with_format" \
  -H "Content-Type: application/json" \
  -d '{
    "xml_string": "<SimpleReport>...</SimpleReport>",
    "format_type": "format2_simple"
  }'
```

### 3. Template Management

#### List Available Templates
```bash
curl "http://localhost:8082/list"
```

#### Fetch Builtin Formats
```bash
curl -X POST "http://localhost:8082/fetch_builtin"
```

## Configuration

The `format_config.json` file contains detailed information about each format, including:
- Format characteristics
- Best use cases
- Data requirements
- Selection guidelines
- LLM instructions

## Testing

### Run All Tests
```bash
# Start services
.\ops\start-services.ps1

# Run tests
.\ops\run-tests.ps1

# Stop services
.\ops\stop-services.ps1
```

### Run Specific Tests
```bash
# Smoke tests
python tests\smoke.py

# XSD format tests
python tests\test_xsd_formats.py

# Full pipeline tests
python tests\full_pipeline.py
```

### Test the Pipeline
```bash
# Run complete pipeline test
.\ops\run-pipeline.ps1
```

## File Structure

```
regulator_xsds/
├── format1_complex.xsd          # Complex comprehensive format
├── format2_simple.xsd           # Simple flat format
├── format_config.json           # Format configuration and metadata
├── complex_pipe_sample.txt      # Sample complex pipe-formatted data
└── README.md                    # This file

services/
├── template_fetcher/            # Downloads and indexes XSD schemas
├── rag/                        # Semantic search over XSD schemas
├── llm_filler/                 # Generates XML using LLM
├── validator/                  # Validates XML against XSD schemas
├── format_selector/            # Analyzes data and recommends format
└── orchestrator/               # Coordinates the complete pipeline
```

## Integration

The XSD formats integrate with the SAR Agent system through:

1. **Format Selector:** Automatically chooses appropriate format
2. **LLM Engine:** Generates XML based on selected format
3. **Report Builder:** Validates against selected schema
4. **File Handler:** Processes pipe-formatted input data
5. **Orchestrator:** Coordinates the complete pipeline

## Support

For questions or issues with the XSD formats:
1. Check the configuration file for format details
2. Use the format selector utility for analysis
3. Review the sample data for examples
4. Consult the LLM instructions in the config file
5. Check service health endpoints for troubleshooting
