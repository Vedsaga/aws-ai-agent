# Diagram 13: Domain Configuration & Templates

## Purpose
Pre-built domain templates for quick deployment (Civic, Agriculture, Disaster).

## Diagram

```mermaid
flowchart TB
    User["User creates domain"]
    
    DomainTemplates["Domain Template Library<br/>Civic Complaints<br/>Agriculture Monitoring<br/>Disaster Response"]
    
    TemplateSelector["Template Selector<br/>Choose pre-built"]
    
    AgentTemplates["Agent Templates<br/>Pre-configured agents<br/>System prompts<br/>Tool permissions"]
    
    PlaybookTemplates["Playbook Templates<br/>Ingestion workflow<br/>Query workflow"]
    
    UITemplates["UI Templates<br/>Map config<br/>Chat config"]
    
    ConfigStore[("DynamoDB<br/>configurations table<br/>Tenant-specific copy")]
    
    User -->|Step 1 Select template| TemplateSelector
    TemplateSelector -->|Step 2 Load template| DomainTemplates
    DomainTemplates -->|Step 3 Get agents| AgentTemplates
    DomainTemplates -->|Step 4 Get playbooks| PlaybookTemplates
    DomainTemplates -->|Step 5 Get UI config| UITemplates
    
    AgentTemplates -->|Step 6 Copy to tenant| ConfigStore
    PlaybookTemplates -->|Step 7 Copy to tenant| ConfigStore
    UITemplates -->|Step 8 Copy to tenant| ConfigStore
    
    ConfigStore -->|Step 9 Ready to use| User

    classDef userBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef templateBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef configBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class User userBox
    class DomainTemplates,TemplateSelector,AgentTemplates,PlaybookTemplates,UITemplates templateBox
    class ConfigStore configBox
```

## Pre-Built Templates

### Civic Complaints Template
- Agents: Geo, Temporal, Entity, Severity Classifier
- Ingestion: Extract location, time, issue type, severity
- Query: When, Where, What, Why agents
- UI: Map with complaint markers, category filters

### Agriculture Monitoring Template
- Agents: Geo, Temporal, Crop Identifier, Weather Analyzer
- Ingestion: Extract farm location, crop type, conditions
- Query: When, Where, What Kind, How Much agents
- UI: Map with farm plots, crop health indicators

### Disaster Response Template
- Agents: Geo, Temporal, Emergency Classifier, Resource Tracker
- Ingestion: Extract incident location, type, urgency, resources needed
- Query: Where, When, What, How Many agents
- UI: Map with emergency markers, resource allocation view
